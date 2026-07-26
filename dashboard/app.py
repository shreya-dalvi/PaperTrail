import os
import sys
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine
from dotenv import load_dotenv

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src', 'agents'))
from analyst_agent import run_analysis

load_dotenv()
engine = create_engine(os.getenv('DATABASE_URL'))

st.set_page_config(page_title="PaperTrail — India Exam Paper Leak Tracker", layout="wide")
st.title("📋 PaperTrail")
st.caption("Autonomous tracking and analysis of exam paper leak incidents in India (2004–2026)")
st.caption(f"Data last refreshed: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')} (cached hourly)")
if st.button("🔄 Refresh data now"):
    st.cache_data.clear()
    st.rerun()

# Load data
@st.cache_data(ttl=3600)
def load_data():
    df = pd.read_sql("SELECT * FROM incidents ORDER BY incident_date DESC", engine)
    df['incident_date'] = pd.to_datetime(df['incident_date'])
    display_cols = ['exam_name', 'conducting_body', 'area', 'state_clean', 'leak_status', 'action_taken']
    df[display_cols] = df[display_cols].fillna("Not specified")
    return df

df = load_data()
analysis = run_analysis()

# Top metrics
col1, col2, col3 = st.columns(3)
col1.metric("Total Incidents Tracked", analysis["total_incidents"])
col2.metric("2027 Forecast", analysis["forecast"].get("2027", "N/A"))
col3.metric("Auto-Detected So Far", len(df[df['confidence'] == 'Auto-Detected']))

st.divider()

# Yearly trend
st.subheader("Incidents per Year")
yearly = pd.Series(analysis["yearly_counts"]).sort_index()
st.bar_chart(yearly)

# Top states
col_a, col_b = st.columns(2)
with col_a:
    st.subheader("Top States by Incidents")
    states = pd.Series(analysis["top_states"]).sort_values()
    st.bar_chart(states)

st.divider()

col_c, col_d = st.columns(2)
with col_c:
    st.subheader("Leak Mechanism Breakdown")
    mech = pd.Series(analysis["mechanism_breakdown"]).sort_values()
    st.bar_chart(mech)
    st.caption("Based on keyword matching in incident notes — many cases remain 'Unspecified' where the mechanism wasn't clearly stated.")

with col_d:
    st.subheader("Top Conducting Bodies")
    bodies = pd.Series(analysis["top_conducting_bodies"]).sort_values()
    st.bar_chart(bodies)

st.divider()

col_e, col_f = st.columns(2)
with col_e:
    st.subheader("Highest-Impact Incidents (by Aspirants Affected)")
    impact_df = pd.DataFrame(analysis["top_impact_incidents"])
    st.dataframe(impact_df, use_container_width=True)

with col_f:
    st.subheader("Era Comparison: UPA vs NDA")
    era_df = pd.DataFrame(analysis["era_comparison"]).T
    st.dataframe(era_df, use_container_width=True)
    st.caption("Normalized by years in office — a more balanced comparison than the 2024 Act analysis, though rising reporting/media attention over time may also contribute to the difference.")

with col_b:
    st.subheader("2024 Act — Before vs After")
    comp = pd.DataFrame(analysis["policy_comparison"])
    st.dataframe(comp)
    st.caption(analysis["post_act_sample_size_note"])

st.divider()

# Latest auto-detected incidents
st.subheader("🔴 Latest Auto-Detected Incidents")
auto_df = df[df['confidence'] == 'Auto-Detected'][
    ['incident_date', 'exam_name', 'state_clean', 'leak_status', 'note', 'source_url']
]
if len(auto_df) > 0:
    st.dataframe(auto_df, use_container_width=True)
else:
    st.info("No auto-detected incidents yet — the Research Agent runs daily via GitHub Actions.")

st.divider()

# Full incident table
st.subheader("Full Incident Log")
st.dataframe(
    df[['incident_id', 'incident_date', 'exam_name', 'state_clean', 'leak_status', 'action_taken', 'source_name']],
    use_container_width=True
)

# Latest report
st.divider()
st.subheader("📄 Latest Policy Brief")
reports_dir = os.path.join(os.path.dirname(__file__), '..', 'reports')
if os.path.exists(reports_dir):
    reports = sorted(os.listdir(reports_dir), reverse=True)
    if reports:
        with open(os.path.join(reports_dir, reports[0]), 'r', encoding='utf-8') as f:
            st.markdown(f.read())
    else:
        st.info("No reports generated yet.")