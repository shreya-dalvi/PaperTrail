import os
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv
from statsmodels.tsa.arima.model import ARIMA

load_dotenv()
engine = create_engine(os.getenv('DATABASE_URL'))

def run_analysis():
    df = pd.read_sql("SELECT * FROM incidents", engine)
    df['incident_date'] = pd.to_datetime(df['incident_date'])
    df['year'] = df['incident_date'].dt.year

    # Yearly trend
    yearly_counts = df.groupby('year').size()

    # Top states
    top_states = df['state_clean'].value_counts().head(10)

    # Before/after 2024 Act comparison
    cutoff = pd.Timestamp('2024-06-01')
    df['post_act'] = df['incident_date'] >= cutoff
    comparison = df.groupby('post_act').agg(
        total_incidents=('incident_id', 'count'),
        arrests_rate=('arrests', lambda x: x.notna().mean()),
        confirmed_rate=('leak_status', lambda x: (x == 'Confirmed').mean())
    )
    comparison.index = ['Before Act (pre-Jun 2024)', 'After Act (post-Jun 2024)']

    # Forecast next 2 years
    ts = yearly_counts.copy()
    ts.index = pd.to_datetime(ts.index, format='%Y')
    ts = ts.asfreq('YS').fillna(0)
    model = ARIMA(ts, order=(1, 1, 1))
    fit = model.fit()
    forecast = fit.forecast(steps=2)

    return {
        "yearly_counts": yearly_counts.to_dict(),
        "top_states": top_states.to_dict(),
        "policy_comparison": comparison.to_dict(),
        "forecast": {str(k.year): round(v, 1) for k, v in forecast.items()},
        "total_incidents": len(df),
        "post_act_sample_size_note": "Post-Act period covers ~2 years vs ~20 years pre-Act — small sample, interpret cautiously"
    }

if __name__ == "__main__":
    results = run_analysis()
    import json
    print(json.dumps(results, indent=2, default=str))