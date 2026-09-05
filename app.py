from pathlib import Path

import streamlit as st

from neuronav.agent import NeuroNavAgent
from neuronav.io import load_trials
from neuronav.models import PatientProfile


DATA_PATH = Path("data/processed/trials_snapshot.csv")

st.set_page_config(page_title="NeuroNav-Agent", page_icon="🧭", layout="wide")
st.title("NeuroNav-Agent")
st.caption("Evidence-grounded navigation for cognitive-health clinical trials")
st.warning(
    "Research prototype only. This tool does not diagnose disease, determine full "
    "eligibility, or replace a clinician or trial coordinator."
)

with st.form("profile"):
    condition = st.text_input("Condition", "Mild Cognitive Impairment")
    col1, col2, col3 = st.columns(3)
    age = col1.number_input("Age", min_value=18, max_value=110, value=65)
    sex = col2.selectbox("Sex used by the registry", ["female", "male"])
    country = col3.text_input("Country", "China")
    submitted = st.form_submit_button("Find potential trials", type="primary")

if submitted:
    if not DATA_PATH.exists():
        st.error("Run scripts/download_trials.py before starting the demo.")
    else:
        profile = PatientProfile(condition, float(age), sex, country)
        report = NeuroNavAgent().navigate(profile, load_trials(DATA_PATH), top_k=5, simulations=1000)
        if not report.ranked_trials:
            st.info("No potential structured matches were found in the snapshot.")
        for item in report.ranked_trials:
            with st.container(border=True):
                st.subheader(f"{item.rank}. {item.trial.title}")
                st.write(
                    f"**{item.trial.nct_id}** · Score {item.decision.base_score:.2f} · "
                    f"Top-5 robustness {item.top_k_probability:.0%}"
                )
                st.write("Registered conditions:", ", ".join(item.trial.conditions))
                st.write("Locations:", ", ".join(item.trial.countries) or "Not reported")
                st.link_button("Open registry record", item.trial.source_url)
                with st.expander("Evidence trace and unresolved checks"):
                    for evidence in item.decision.evidence:
                        st.write(f"- **{evidence.check} / {evidence.outcome}:** {evidence.explanation}")
                    for limitation in item.decision.unresolved:
                        st.write(f"- {limitation}")

