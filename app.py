import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# 1. Page Configuration
st.set_page_config(page_title="My Strava Dashboard", page_icon="🏃‍♂️", layout="wide")
st.title("🏃‍♂️ Personal Strava Performance Dashboard")
st.markdown("Welcome to my automated running analysis platform.")


# 2. Load and Clean Data (Cached so it's fast!)
@st.cache_data
def load_data():
    df = pd.read_csv('activities.csv')
    df['Activity Date'] = pd.to_datetime(df['Activity Date'], format='mixed')

    # Filter for Runs with valid speed
    runs = df[(df['Activity Type'] == 'Run') & (df['Average Speed'] > 0)].copy()

    # Calculate Pace and Miles
    runs['Pace_min_per_mile'] = 60 / (runs['Average Speed'] * 2.23694)
    runs['Distance_miles'] = runs['Distance'] * 0.000621371

    # Remove extreme outliers using percentiles
    q1 = runs['Pace_min_per_mile'].quantile(0.10)
    q3 = runs['Pace_min_per_mile'].quantile(0.90)
    clean_runs = runs[(runs['Pace_min_per_mile'] >= q1) & (runs['Pace_min_per_mile'] <= q3)].copy()

    return clean_runs.sort_values('Activity Date')


df = load_data()

# 3. Sidebar Filters
st.sidebar.header("Dashboard Filters")
min_distance = st.sidebar.slider("Minimum Distance (miles)", 0.0, 20.0, 1.0, 0.5)
days_back = st.sidebar.slider("Days of History", 30, 365, 365, 30)

# Apply filters
cutoff_date = pd.Timestamp.now() - pd.Timedelta(days=days_back)
filtered_df = df[(df['Distance_miles'] >= min_distance) & (df['Activity Date'] >= cutoff_date)]

# 4. Top-Level Metrics
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Runs Analyzed", len(filtered_df))
with col2:
    st.metric("Total Miles Logged", f"{filtered_df['Distance_miles'].sum():.1f} mi")
with col3:
    if len(filtered_df) > 0:
        avg_pace = filtered_df['Pace_min_per_mile'].mean()
        st.metric("Average Pace Overall", f"{int(avg_pace)}:{int((avg_pace % 1) * 60):02d} /mi")
    else:
        st.metric("Average Pace Overall", "N/A")

st.markdown("---")

# 5. Interactive Chart
st.subheader("Pace Progression Over Time")
if len(filtered_df) > 2:
    fig = px.scatter(
        filtered_df,
        x='Activity Date',
        y='Pace_min_per_mile',
        size='Distance_miles',
        color='Distance_miles',
        hover_name='Activity Name',
        color_continuous_scale='Viridis',
        trendline="ols",
        trendline_color_override="red"
    )
    fig.update_layout(yaxis_autorange="reversed")  # Reverses Y-axis so faster paces (lower numbers) are at the top!
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("Not enough data points to map a trendline. Adjust your filters!")

# 6. Raw Data Table
st.subheader("Raw Run Data")
st.dataframe(
    filtered_df[['Activity Date', 'Activity Name', 'Distance_miles', 'Pace_min_per_mile']].sort_values('Activity Date',

import pandas as pd

# Check if avg_pace is NaN before trying to format it
if pd.isna(avg_pace):
    st.metric("Average Pace Overall", "N/A")
else:
    st.metric("Average Pace Overall", f"{int(avg_pace)}:{int((avg_pace % 1) * 60):02d} /mi")
ascending=False))