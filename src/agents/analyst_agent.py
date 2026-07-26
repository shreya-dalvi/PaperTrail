import os
import re
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv
from statsmodels.tsa.arima.model import ARIMA

load_dotenv()
engine = create_engine(os.getenv('DATABASE_URL'))

MECHANISM_KEYWORDS = {
    "Impersonation/Solver": ["impersonat", "solver", "proxy", "stand-in"],
    "Insider Leak": ["insider", "official", "employee", "staff"],
    "Printing/Press Leak": ["printing", "press"],
    "Tech-enabled (device/OMR)": ["omr", "device", "camera", "bluetooth", "electronic"],
    "Social Media/WhatsApp Circulation": ["whatsapp", "telegram", "social media"],
}

def classify_mechanism(note):
    if not isinstance(note, str):
        return "Unspecified"
    note_lower = note.lower()
    for label, keywords in MECHANISM_KEYWORDS.items():
        if any(kw in note_lower for kw in keywords):
            return label
    return "Unspecified"

def run_analysis():
    df = pd.read_sql("SELECT * FROM incidents", engine)
    df['incident_date'] = pd.to_datetime(df['incident_date'])
    df['year'] = df['incident_date'].dt.year

    # 1. Yearly trend
    yearly_counts = df.groupby('year').size()

    # 2. Top states
    top_states = df['state_clean'].value_counts().head(10)

    # 3. Before/after 2024 Act
    cutoff = pd.Timestamp('2024-06-01')
    df['post_act'] = df['incident_date'] >= cutoff
    comparison = df.groupby('post_act').agg(
        total_incidents=('incident_id', 'count'),
        arrests_rate=('arrests', lambda x: x.notna().mean()),
        confirmed_rate=('leak_status', lambda x: (x == 'Confirmed').mean())
    )
    comparison.index = ['Before Act (pre-Jun 2024)', 'After Act (post-Jun 2024)']

    # 4. Forecast
    ts = yearly_counts.copy()
    ts.index = pd.to_datetime(ts.index, format='%Y')
    ts = ts.asfreq('YS').fillna(0)
    model = ARIMA(ts, order=(1, 1, 1))
    fit = model.fit()
    forecast = fit.forecast(steps=2)

    # 5. NEW: Leak mechanism breakdown (keyword-based classification of `note`)
    df['mechanism'] = df['note'].apply(classify_mechanism)
    mechanism_counts = df['mechanism'].value_counts()

    # 6. NEW: Conducting body analysis
    top_conducting_bodies = df['conducting_body'].value_counts().head(10)

    # 7. NEW: Aspirants affected — top 10 highest-impact incidents
    impact_df = df[df['aspirants_affected'].notna()].sort_values('aspirants_affected', ascending=False).head(10)
    top_impact = impact_df[['exam_name', 'state_clean', 'aspirants_affected']].to_dict('records')

    # 8. NEW: Era comparison (UPA vs NDA) — more balanced sample than Act comparison
    era_comparison = df.groupby('era').agg(
        total_incidents=('incident_id', 'count'),
        avg_per_year=('incident_id', 'count')  # placeholder, corrected below
    )
    era_years = {
        "UPA (2004-May2014)": 10,   # 2004-2014
        "NDA (May2014-now)": (df['year'].max() - 2014) + 1
    }
    era_comparison['years_span'] = era_comparison.index.map(era_years)
    era_comparison['avg_per_year'] = (era_comparison['total_incidents'] / era_comparison['years_span']).round(2)
    era_comparison = era_comparison.drop(columns=['avg_per_year']).join(
        (era_comparison['total_incidents'] / era_comparison['years_span']).round(2).rename('avg_per_year')
    )

    return {
        "yearly_counts": yearly_counts.to_dict(),
        "top_states": top_states.to_dict(),
        "policy_comparison": comparison.to_dict(),
        "forecast": {str(k.year): round(v, 1) for k, v in forecast.items()},
        "total_incidents": len(df),
        "post_act_sample_size_note": "Post-Act period covers ~2 years vs ~20 years pre-Act — small sample, interpret cautiously",
        "mechanism_breakdown": mechanism_counts.to_dict(),
        "top_conducting_bodies": top_conducting_bodies.to_dict(),
        "top_impact_incidents": top_impact,
        "era_comparison": era_comparison[['total_incidents', 'years_span', 'avg_per_year']].to_dict('index'),
    }

if __name__ == "__main__":
    results = run_analysis()
    import json
    print(json.dumps(results, indent=2, default=str))