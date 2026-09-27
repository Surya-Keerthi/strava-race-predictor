# 🏃 Strava Performance Dashboard & ML Race Predictor

An automated, effort-adjusted race time prediction engine and performance dashboard built with **Streamlit**, **Scikit-Learn**, and **Plotly**.

## 📌 Features

- **25th-Percentile Peak Effort Filtering:** Isolates max-effort runs to eliminate bias from low-intensity Zone 2 recovery runs.
- **Logarithmic Distance Decay Model:** Models non-linear aerobic fatigue across race distances using logarithmic feature scaling.
- **Weighted Least Squares (WLS):** Prioritizes high-output effort points by weighting observations by distance and speed.
- **Endurance Volume Scaling:** Dynamically adjusts race distance projections based on recent long-run volume.
- **Interactive Visualizations:** Displays interactive pace decay curves and custom target race metrics.

## 🚀 Quickstart

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/YOUR_USERNAME/strava-race-predictor.git](https://github.com/YOUR_USERNAME/strava-race-predictor.git)
   cd strava-race-predictor
   pip install -r requirements.txt
   streamlit run Strava_Full_Project.py
   