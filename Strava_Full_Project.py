import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sklearn.linear_model import LinearRegression
import numpy as np

# 1. Page Configuration & Strava Custom Styling
st.set_page_config(page_title="Strava Performance Dashboard", page_icon="🏃‍♂️", layout="wide")

# Inject Custom CSS for Strava Orange Theme (#FC4C02)
st.markdown("""
    <style>
    /* Primary Strava Branding Colors */
    h1, h2, h3 { color: #FC4C02 !important; font-family: 'Helvetica Neue', sans-serif; }
    div[data-testid="stMetricValue"] { color: #FC4C02 !important; font-weight: bold; }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] { background-color: #1E1E24; }

    /* Custom Accent Lines */
    hr { border-top: 2px solid #FC4C02 !important; }
    </style>
""", unsafe_allow_html=True)

st.title("🏃‍♂️ STRAVA PERFORMANCE DASHBOARD")
st.markdown("Automated run analysis platform styled in classic Strava Orange.")


# 2. Load and Clean Data with Auto-Unit Detection
# 2. Load and Clean Data with Exact Unit Detection
@st.cache_data
def load_data():
    try:
        df = pd.read_csv('activities.csv')
        df['Activity Date'] = pd.to_datetime(df['Activity Date'], format='mixed')

        # Filter for valid runs
        runs = df[(df['Activity Type'] == 'Run') & (df['Average Speed'] > 0)].copy()

        # Calculate Pace (min/mile) from Average Speed (m/s)
        runs['Pace_min_per_mile'] = 60 / (runs['Average Speed'] * 2.23694)

        # Exact Unit Detection using Speed and Time
        time_col = 'Moving Time' if 'Moving Time' in runs.columns else 'Elapsed Time'
        expected_meters = runs['Average Speed'] * runs[time_col]
        unit_ratio = (expected_meters / runs['Distance']).median()

        if 800 < unit_ratio < 1200:
            # CSV distance is in Kilometers (e.g., 19.34 km -> 12.01 mi)
            runs['Distance_miles'] = runs['Distance'] * 0.621371
        elif 0.8 < unit_ratio < 1.2:
            # CSV distance is in Meters (e.g., 19340 m -> 12.01 mi)
            runs['Distance_miles'] = runs['Distance'] * 0.000621371
        else:
            # CSV distance is already in Miles
            runs['Distance_miles'] = runs['Distance']

            # Calculate Effort-Adjusted Weight (Distance * Speed)
            runs['speed_mph'] = 60 / runs['Pace_min_per_mile']
            runs['wls_weight'] = runs['Distance_miles'] * runs['speed_mph']

        # Remove extreme pace outliers (top/bottom 5%)
        q1 = runs['Pace_min_per_mile'].quantile(0.05)
        q3 = runs['Pace_min_per_mile'].quantile(0.95)
        clean_runs = runs[(runs['Pace_min_per_mile'] >= q1) & (runs['Pace_min_per_mile'] <= q3)].copy()

        return clean_runs.sort_values('Activity Date')
    except Exception as e:
        st.error(f"Error loading CSV file: {e}")
        return pd.DataFrame()


def predict_race_times(df):
    import numpy as np
    from sklearn.linear_model import LinearRegression

    df['Activity Date'] = pd.to_datetime(df['Activity Date'])

    # 1. Feature Engineering: 6-week rolling window
    max_date = df['Activity Date'].max()
    six_weeks_ago = max_date - pd.Timedelta(days=42)
    recent_df = df[df['Activity Date'] >= six_weeks_ago].copy()

    if recent_df.empty:
        return None

    recent_df['speed_mph'] = 60 / recent_df['Pace_min_per_mile']
    recent_df['weighted_pace'] = recent_df['Pace_min_per_mile'] * recent_df['Distance_miles']
    six_week_weighted_pace = recent_df['weighted_pace'].sum() / recent_df['Distance_miles'].sum()
    weekly_frequency = len(recent_df) / 6.0
    max_long_run = recent_df['Distance_miles'].max()

    # 2. Filter for Top Performance (25th Percentile)
    valid_runs = df[df['Distance_miles'] >= 1.0].copy()
    pace_cutoff = valid_runs['Pace_min_per_mile'].quantile(0.25)
    fast_runs = valid_runs[valid_runs['Pace_min_per_mile'] <= pace_cutoff].copy()
    training_set = fast_runs if len(fast_runs) >= 5 else valid_runs

    # 3. Fit Non-Linear Logarithmic Distance Model (X = ln(Distance))
    X_train = np.log(training_set[['Distance_miles']].values)
    y_train = training_set['Pace_min_per_mile'].values

    training_set['speed_mph'] = 60 / training_set['Pace_min_per_mile']
    training_set['wls_weight'] = training_set['Distance_miles'] * training_set['speed_mph']
    weights = training_set['wls_weight'].values

    model = LinearRegression()
    model.fit(X_train, y_train, sample_weight=weights)

    # 4. Target Distances & Predictions
    races = {"5K": 3.10686, "10K": 6.21371, "Half Marathon": 13.1094, "Marathon": 26.2188}
    predictions = {}

    for race_name, dist in races.items():
        base_pace = model.predict(np.array([[np.log(dist)]]))[0]
        endurance_factor = max(0.85, 1.0 - (max_long_run / (dist * 2)) * 0.05)
        adjusted_pace = base_pace * endurance_factor

        total_minutes = adjusted_pace * dist
        hours, mins = int(total_minutes // 60), int(total_minutes % 60)
        secs = int((total_minutes * 60) % 60)
        time_str = f"{hours}h {mins:02d}m {secs:02d}s" if hours > 0 else f"{mins}m {secs:02d}s"

        predictions[race_name] = {
            "time": time_str,
            "pace": f"{adjusted_pace:.2f} min/mi",
            "dist": dist,
            "raw_pace": adjusted_pace
        }

    # 5. Continuous Non-Linear Decay Curve (Matching Dot Endurance Adjustments)
    curve_distances = np.linspace(1.0, 26.2, 50)
    curve_paces = []
    for d in curve_distances:
        base_p = model.predict(np.array([[np.log(d)]]))[0]
        e_factor = max(0.85, 1.0 - (max_long_run / (d * 2)) * 0.05)
        curve_paces.append(base_p * e_factor)

    return predictions, six_week_weighted_pace, weekly_frequency, max_long_run, curve_distances, curve_paces
df = load_data()

if df.empty:
    st.warning("No run data found in activities.csv.")
else:
    # 3. Sidebar Filters
    st.sidebar.header("🍊 Dashboard Filters")
    max_run_length = float(df['Distance_miles'].max()) if not df.empty else 20.0

    min_distance = st.sidebar.slider("Minimum Distance (miles)", 0.0, round(max_run_length, 1), 1.0, 0.5)
    days_back = st.sidebar.slider("Days of History", 30, 365, 365, 30)

    # Filter Dataset
    cutoff_date = pd.Timestamp.now() - pd.Timedelta(days=days_back)
    filtered_df = df[(df['Distance_miles'] >= min_distance) & (df['Activity Date'] >= cutoff_date)]

    tab1, tab2 = st.tabs(["📊 Analytics Dashboard", "🤖 ML Race Predictor"])

    with tab1:
        # (Keep your existing Pace Progression chart and Activity History dataframe here)
        pass

    with tab2:
        st.subheader("🤖 Scikit-Learn Race Time Predictor")

        results = predict_race_times(df)
        if results:
            preds, avg_p, freq, long_r, curve_dists, curve_paces = results

            # 1. Rolling 6-Week Feature Matrix
            c1, c2, c3 = st.columns(3)
            c1.metric("6-Wk Weighted Pace", f"{avg_p:.2f} min/mi")
            c2.metric("Weekly Frequency", f"{freq:.1f} runs/wk")
            c3.metric("Max Long Run", f"{long_r:.1f} mi")

            st.markdown("---")

            # 2. Race Prediction Metric Cards
            p_cols = st.columns(4)
            for idx, (race, info) in enumerate(preds.items()):
                with p_cols[idx]:
                    st.metric(label=race, value=info["time"], delta=f"Pace: {info['pace']}")

            st.markdown("---")

            # 3. Predicted Distance-Decay Pace Curve
            st.subheader("📈 Predicted Race Pace Decay Curve")
            fig_curve = go.Figure()

            # Continuous theoretical decay line
            fig_curve.add_trace(go.Scatter(
                x=curve_dists, y=curve_paces,
                mode='lines', name='Theoretical Decay Curve',
                line=dict(color='#FC4C02', width=3)
            ))

            # Target race marker points
            race_dists = [info['dist'] for info in preds.values()]
            race_paces = [info['raw_pace'] for info in preds.values()]
            race_labels = list(preds.keys())

            fig_curve.add_trace(go.Scatter(
                x=race_dists, y=race_paces,
                mode='markers+text', name='Race Targets',
                text=race_labels, textposition="top center",
                marker=dict(size=12, color='#FFFFFF', line=dict(width=2, color='#FC4C02'))
            ))

            fig_curve.update_layout(
                template="plotly_dark",
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                xaxis_title="Race Distance (miles)",
                yaxis_title="Predicted Pace (min/mile)",
                yaxis_autorange="reversed"  # Faster pace at top
            )
            st.plotly_chart(fig_curve, use_container_width=True)

    # 4. Top-Level Strava Metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Runs", len(filtered_df))
    with col2:
        st.metric("Total Distance", f"{filtered_df['Distance_miles'].sum():.1f} mi")
    with col3:
        if len(filtered_df) > 0:
            avg_pace = filtered_df['Pace_min_per_mile'].mean()
            if pd.notna(avg_pace):
                mins = int(avg_pace)
                secs = int((avg_pace % 1) * 60)
                st.metric("Average Pace", f"{mins}:{secs:02d} /mi")
            else:
                st.metric("Average Pace", "N/A")
        else:
            st.metric("Average Pace", "N/A")

    st.markdown("---")

    # 5. Interactive Strava Chart (Distance-Weighted Regression)
    st.subheader("Pace Progression Over Time")
    if len(filtered_df) >= 2:
        import numpy as np
        import plotly.graph_objects as go
        from sklearn.linear_model import LinearRegression

        # 1. Prepare features (X) and target (y) from filtered_df
        X = filtered_df[['Distance_miles']].values
        y = filtered_df['Pace_min_per_mile'].values
        # 1. Prepare features (X) and target (y) from filtered_df
        X = filtered_df[['Distance_miles']].values
        y = filtered_df['Pace_min_per_mile'].values

        filtered_df['speed_mph'] = 60 / filtered_df['Pace_min_per_mile']
        filtered_df['wls_weight'] = filtered_df['Distance_miles'] * filtered_df['speed_mph']

        weights = filtered_df['wls_weight'].values
        weights = filtered_df['wls_weight'].values

        # 2. Fit WLS model using our effort weights
        wls_model = LinearRegression()
        wls_model.fit(X, y, sample_weight=weights)

        # 3. Create predictions for trendline
        filtered_df['wls_trendline'] = wls_model.predict(X)

        # Base scatter plot
        fig = px.scatter(
            filtered_df,
            x='Activity Date',
            y='Pace_min_per_mile',
            size='Distance_miles',
            color='Distance_miles',
            hover_name='Activity Name',
            labels={'Pace_min_per_mile': 'Pace (min/mi)', 'Distance_miles': 'Miles'},
            color_continuous_scale=['#FFC2A6', '#FC4C02', '#B33000']
        )

        # Calculate Weighted Least Squares (WLS) Trendline using run distance as weights
        x_days = (filtered_df['Activity Date'] - filtered_df['Activity Date'].min()).dt.total_seconds() / 86400.0
        weights = filtered_df['Distance_miles']

        # Fit degree 1 polynomial weighted by run mileage
        slope, intercept = np.polyfit(x_days, filtered_df['Pace_min_per_mile'], 1, w=weights)
        trend_y = slope * x_days + intercept

        # Add distance-weighted trendline to the plot
        fig.add_trace(go.Scatter(
            x=filtered_df['Activity Date'],
            y=trend_y,
            mode='lines',
            name='Distance-Weighted Trend',
            line=dict(color='#FFFFFF', width=3, dash='dash')
        ))

        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            yaxis_autorange="reversed"  # Faster pace at top
        )
        st.plotly_chart(fig, use_container_width=True)

    # 6. Raw Data Table
    st.subheader("Activity History")
    st.dataframe(
        filtered_df[['Activity Date', 'Activity Name', 'Distance_miles', 'Pace_min_per_mile']]
        .rename(columns={'Distance_miles': 'Distance (mi)', 'Pace_min_per_mile': 'Pace (min/mi)'})
        .sort_values('Activity Date', ascending=False),
        use_container_width=True
    )