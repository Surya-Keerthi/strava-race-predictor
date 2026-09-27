import pandas as pd
import numpy as np
import plotly.express as px
from scipy import stats


class StravaAnalyzer:
    """A data analysis pipeline for Strava activity performance tracking."""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.raw_df = pd.DataFrame()
        self.clean_df = pd.DataFrame()

    def load_and_preprocess(self, days: int = 365) -> pd.DataFrame:
        """Loads CSV, filters activity types, and calculates metrics."""
        self.raw_df = pd.read_csv(self.file_path)

        # Convert dates and filter timeframe
        self.raw_df['Activity Date'] = pd.to_datetime(self.raw_df['Activity Date'], format='mixed')
        cutoff_date = pd.Timestamp.now() - pd.Timedelta(days=days)

        # Filter for valid runs
        runs = self.raw_df[
            (self.raw_df['Activity Type'] == 'Run') &
            (self.raw_df['Activity Date'] >= cutoff_date) &
            (self.raw_df['Average Speed'] > 0)
            ].copy()

        # Feature Engineering: Derive pace and miles
        runs['Pace_min_mile'] = 60 / (runs['Average Speed'] * 2.23694)
        runs['Distance_miles'] = runs['Distance'] * 0.000621371

        # Outlier Removal using Interquartile Range (IQR)
        q1 = runs['Pace_min_mile'].quantile(0.10)
        q3 = runs['Pace_min_mile'].quantile(0.90)
        self.clean_df = runs[(runs['Pace_min_mile'] >= q1) & (runs['Pace_min_mile'] <= q3)].copy()
        self.clean_df.sort_values('Activity Date', inplace=True)

        # Add 30-day rolling average
        self.clean_df['30D_Rolling_Pace'] = self.clean_df['Pace_min_mile'].rolling(window=5, min_periods=1).mean()
        return self.clean_df

    def Perform_statistical_analysis(self) -> dict:
        """Calculates linear regression trend and p-value for significance."""
        x = pd.to_numeric(self.clean_df['Activity Date']) / 10 ** 9  # Convert to epoch seconds
        y = self.clean_df['Pace_min_mile']

        slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)

        return {
            "r_squared": r_value ** 2,
            "p_value": p_value,
            "statistically_significant": p_value < 0.05,
            "slope": slope
        }

    def generate_interactive_plot(self, output_html: str = "strava_dashboard.html"):
        """Generates an interactive HTML plot using Plotly."""
        fig = px.scatter(
            self.clean_df,
            x='Activity Date',
            y='Pace_min_mile',
            size='Distance_miles',
            hover_data=['Activity Name', 'Distance_miles'],
            title="Strava Performance Trends (Hover for Details)",
            labels={'Pace_min_mile': 'Pace (min/mi)', 'Activity Date': 'Date'},
            trendline="ols",
            trendline_color_override="red"
        )

        fig.update_layout(template="plotly_dark")
        fig.write_html(output_html)
        print(f"📊 Interactive dashboard saved to {output_html}")


if __name__ == "__main__":
    analyzer = StravaAnalyzer('activities.csv')
    df = analyzer.load_and_preprocess()
    stats_results = analyzer.Perform_statistical_analysis()

    print("\n--- PROFESSIONAL SUMMARY ---")
    print(f"Data points processed: {len(df)}")
    print(f"R-Squared (Model Fit): {stats_results['r_squared']:.4f}")
    print(f"P-Value (Significance): {stats_results['p_value']:.4f}")
    print(f"Pace change statistically significant? {stats_results['statistically_significant']}")

    analyzer.generate_interactive_plot()