from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

import pandas as pd
import requests
import streamlit as st

API_BASE_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="Diabetes Mobile Risk Assessment",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .hero {
        background: linear-gradient(135deg, #0f172a 0%, #115e59 52%, #0f766e 100%);
        color: white;
        padding: 1.4rem 1.6rem;
        border-radius: 18px;
        box-shadow: 0 18px 45px rgba(15, 23, 42, 0.25);
        margin-bottom: 1rem;
    }
    .hero h1 { margin: 0; font-size: 2rem; }
    .hero p { margin: 0.35rem 0 0 0; opacity: 0.9; }
    .card {
        background: rgba(255, 255, 255, 0.92);
        border: 1px solid rgba(15, 118, 110, 0.15);
        border-radius: 16px;
        padding: 1rem 1.1rem;
        box-shadow: 0 10px 28px rgba(15, 23, 42, 0.06);
        margin-bottom: 1rem;
    }
    .status-low {
        background: #ecfdf5;
        color: #065f46;
        border-left: 6px solid #10b981;
        padding: 1rem;
        border-radius: 14px;
    }
    .status-medium {
        background: #fffbeb;
        color: #92400e;
        border-left: 6px solid #f59e0b;
        padding: 1rem;
        border-radius: 14px;
    }
    .status-high {
        background: #fef2f2;
        color: #991b1b;
        border-left: 6px solid #ef4444;
        padding: 1rem;
        border-radius: 14px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

if "user_id" not in st.session_state:
    st.session_state.user_id = ""
if "session_id" not in st.session_state:
    st.session_state.session_id = ""
if "profile_saved" not in st.session_state:
    st.session_state.profile_saved = False
if "profile_user_id" not in st.session_state:
    st.session_state.profile_user_id = ""
if "logs_received" not in st.session_state:
    st.session_state.logs_received = 0
if "latest_prediction" not in st.session_state:
    st.session_state.latest_prediction = None


def api_get(path: str, timeout: int = 10) -> requests.Response:
    return requests.get(f"{API_BASE_URL}{path}", timeout=timeout)


def api_post(path: str, payload: Optional[Dict[str, Any]] = None, timeout: int = 15) -> requests.Response:
    return requests.post(f"{API_BASE_URL}{path}", json=payload, timeout=timeout)


def refresh_health() -> Dict[str, Any]:
    response = api_get("/health", timeout=5)
    response.raise_for_status()
    return response.json()


def refresh_session_status() -> Optional[Dict[str, Any]]:
    if not st.session_state.session_id:
        return None
    response = api_get(f"/sessions/{st.session_state.session_id}")
    response.raise_for_status()
    data = response.json()
    st.session_state.logs_received = data.get("days_received", 0)
    return data


def load_latest_prediction() -> Optional[Dict[str, Any]]:
    if not st.session_state.user_id:
        return None
    response = api_get(f"/users/{st.session_state.user_id}/prediction/latest")
    if response.status_code == 404:
        return None
    response.raise_for_status()
    return response.json()


st.markdown(
    """
    <div class="hero">
        <h1>🏥 Diabetes Mobile Risk Assessment</h1>
        <p>Collect profile details once, capture 3 consecutive daily health logs, and get a risk score.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.sidebar.markdown("### Navigation")
page = st.sidebar.radio("Workflow", ["Setup", "Daily Logs", "Assessment", "Metrics", "Retrain"])

st.sidebar.markdown("---")
st.sidebar.markdown("### API Status")
try:
    health = refresh_health()
    st.sidebar.success("Backend connected")
    st.sidebar.caption(f"API: {health.get('api_version', 'n/a')}")
    st.sidebar.caption(f"Workflow: {health.get('workflow_version', 'n/a')}")
    st.sidebar.caption(f"Model loaded: {health.get('model_loaded', False)}")
except Exception:
    st.sidebar.error("Cannot reach FastAPI backend")

st.sidebar.markdown("---")
st.sidebar.markdown("### Current State")
st.sidebar.write(f"User ID: {st.session_state.user_id or 'not set'}")
st.sidebar.write(f"Session ID: {st.session_state.session_id or 'not started'}")
st.sidebar.write(f"Logs received: {st.session_state.logs_received}/3")


def submit_profile() -> None:
    user_id = st.session_state.user_id.strip()
    if not user_id:
        raise ValueError("Enter a user ID before saving the profile.")

    payload = {
        "user_id": user_id,
        "age": int(st.session_state.age),
        "bmi": float(st.session_state.bmi),
        "sex": st.session_state.sex,
    }
    response = api_post("/profile", payload)
    response.raise_for_status()
    st.session_state.profile_saved = True
    st.session_state.profile_user_id = user_id


def start_session() -> None:
    user_id = st.session_state.user_id.strip()
    if not user_id:
        raise ValueError("Enter a user ID before starting a session.")

    response = api_post("/sessions", {"user_id": user_id})
    response.raise_for_status()
    data = response.json()
    st.session_state.session_id = data["session_id"]
    st.session_state.logs_received = data.get("days_received", 0)


def submit_day(day: int, payload: Dict[str, Any]) -> None:
    response = api_post(f"/sessions/{st.session_state.session_id}/daily-log", {"day": day, **payload})
    response.raise_for_status()
    data = response.json()
    st.session_state.logs_received = data.get("days_received", st.session_state.logs_received)


def run_assessment() -> Dict[str, Any]:
    response = api_post(f"/sessions/{st.session_state.session_id}/predict", payload={})
    response.raise_for_status()
    data = response.json()
    st.session_state.latest_prediction = data
    return data


if page == "Setup":
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("1. Create Profile and Start Session")
    st.caption("Collect one-time profile inputs, then open a new 3-day assessment session.")

    col1, col2 = st.columns(2)
    with col1:
        st.session_state.user_id = st.text_input("User ID", value=st.session_state.user_id, placeholder="patient_001")
        st.session_state.age = st.number_input("Age", min_value=1, max_value=120, value=40, step=1)
        st.session_state.bmi = st.number_input("BMI", min_value=10.0, max_value=60.0, value=28.0, step=0.1)
    with col2:
        st.session_state.sex = st.selectbox("Sex", ["male", "female", "other"], index=0)
        save_clicked = st.button("Save Profile", use_container_width=True)
        start_clicked = st.button("Start Assessment Session", use_container_width=True, type="primary")

    current_user_id = st.session_state.user_id.strip()
    if st.session_state.profile_saved and st.session_state.profile_user_id and current_user_id != st.session_state.profile_user_id:
        st.warning("User ID changed. Save the new profile before starting a session.")
        st.session_state.profile_saved = False
        st.session_state.session_id = ""
        st.session_state.logs_received = 0

    if save_clicked:
        try:
            submit_profile()
            st.success("Profile saved.")
        except Exception as exc:
            st.error(f"Could not save profile: {exc}")

    if start_clicked:
        try:
            if not st.session_state.profile_saved or st.session_state.profile_user_id != current_user_id:
                submit_profile()
            start_session()
            st.success(f"Session started: {st.session_state.session_id}")
        except Exception as exc:
            st.error(f"Could not start session: {exc}")

    st.markdown("</div>", unsafe_allow_html=True)

elif page == "Daily Logs":
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("2. Collect Daily Logs for 3 Consecutive Days")
    st.caption("Submit one log per day. Day order matters.")

    if not st.session_state.session_id:
        st.warning("Start a session first in the Setup page.")
    else:
        try:
            status = refresh_session_status()
            if status:
                st.write(f"Session status: **{status.get('status')}** | Days received: **{status.get('days_received', 0)}/3**")
        except Exception as exc:
            st.warning(f"Could not refresh session status: {exc}")

        tabs = st.tabs(["Day 1", "Day 2", "Day 3"])
        for index, tab in enumerate(tabs, start=1):
            with tab:
                with st.form(f"day_form_{index}"):
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        urination_frequency = st.number_input("Urination frequency", min_value=0, max_value=30, value=6 + index, step=1, key=f"ur_{index}")
                        thirst_frequency = st.number_input("Thirst frequency", min_value=0, max_value=30, value=4 + index, step=1, key=f"tf_{index}")
                    with c2:
                        thirst_level = st.slider("Thirst level", 1, 4, 2 if index == 1 else 3, key=f"tl_{index}")
                        fatigue_level = st.slider("Fatigue level", 1, 5, 2 if index == 1 else 3, key=f"fl_{index}")
                    with c3:
                        physical_activity = st.checkbox("Physical activity", value=index != 2, key=f"pa_{index}")
                        alcohol_consumption = st.checkbox("Alcohol consumption", value=False, key=f"al_{index}")
                        smoking = st.checkbox("Smoking", value=False, key=f"sm_{index}")

                    submitted = st.form_submit_button(f"Submit Day {index}", use_container_width=True)
                    if submitted:
                        try:
                            submit_day(
                                index,
                                {
                                    "urination_frequency": int(urination_frequency),
                                    "thirst_frequency": int(thirst_frequency),
                                    "thirst_level": int(thirst_level),
                                    "fatigue_level": int(fatigue_level),
                                    "physical_activity": bool(physical_activity),
                                    "alcohol_consumption": bool(alcohol_consumption),
                                    "smoking": bool(smoking),
                                },
                            )
                            st.success(f"Day {index} saved.")
                        except Exception as exc:
                            st.error(f"Could not save Day {index}: {exc}")
    st.markdown("</div>", unsafe_allow_html=True)

elif page == "Assessment":
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("3. Run Assessment")
    st.caption("Prediction becomes available after 3 completed daily logs.")

    if not st.session_state.session_id:
        st.warning("Start a session first.")
    else:
        try:
            status = refresh_session_status()
            if status:
                st.write(status)
                if status.get("session_complete"):
                    st.success("Assessment already completed.")
                elif status.get("days_received", 0) < 3:
                    st.info("Collect all 3 daily logs before prediction.")
                else:
                    if st.button("Run Prediction", type="primary", use_container_width=True):
                        try:
                            result = run_assessment()
                            risk_level = result["risk_level"]
                            probability = float(result["probability"])
                            st.markdown(
                                f"<div class='status-{risk_level.lower()}'><h3>Risk Level: {risk_level}</h3><p>Probability: {probability:.2%}</p></div>",
                                unsafe_allow_html=True,
                            )
                            st.write("**Explanation**")
                            for item in result.get("explanation", []):
                                st.write(f"- {item}")
                        except Exception as exc:
                            st.error(f"Prediction failed: {exc}")
        except Exception as exc:
            st.error(f"Could not load session status: {exc}")

        if st.session_state.latest_prediction:
            st.markdown("---")
            st.write("Latest prediction:")
            st.json(st.session_state.latest_prediction)

    st.markdown("</div>", unsafe_allow_html=True)

elif page == "Metrics":
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Model Metrics")
    st.caption("View model performance from the backend.")

    if st.button("Refresh Metrics", use_container_width=True):
        try:
            response = api_get("/metrics")
            response.raise_for_status()
            metrics = response.json()
            st.write(f"Best model: **{metrics.get('best_model', 'n/a')}**")
            selected = metrics.get("selected_metrics", {})
            cols = st.columns(5)
            cols[0].metric("Accuracy", f"{selected.get('accuracy', 0):.4f}")
            cols[1].metric("Precision", f"{selected.get('precision', 0):.4f}")
            cols[2].metric("Recall", f"{selected.get('recall', 0):.4f}")
            cols[3].metric("F1", f"{selected.get('f1_score', 0):.4f}")
            cols[4].metric("ROC-AUC", f"{selected.get('roc_auc', 0):.4f}")
            metrics_frame = pd.DataFrame(metrics.get("all_model_metrics", []))
            if not metrics_frame.empty:
                st.dataframe(metrics_frame, use_container_width=True, hide_index=True)
                st.bar_chart(metrics_frame.set_index("model")[["accuracy", "f1_score"]])
        except Exception as exc:
            st.error(f"Could not load metrics: {exc}")

    st.markdown("</div>", unsafe_allow_html=True)

elif page == "Retrain":
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Retrain Model")
    st.caption("Trigger retraining from the backend using the current workbook.")

    if st.button("Run Retrain", type="primary", use_container_width=True):
        try:
            response = api_post("/retrain", payload={"force": True}, timeout=300)
            response.raise_for_status()
            data = response.json()
            st.success("Retraining completed.")
            st.json(data)
        except Exception as exc:
            st.error(f"Retrain failed: {exc}")

    st.markdown("</div>", unsafe_allow_html=True)

latest = load_latest_prediction()
st.sidebar.markdown("---")
st.sidebar.markdown("### Latest Prediction")
if latest:
    st.sidebar.write(f"Risk: {latest.get('risk_level', 'n/a')}")
    st.sidebar.write(f"Probability: {float(latest.get('probability', 0.0)):.2%}")
else:
    st.sidebar.caption("No prediction yet")
