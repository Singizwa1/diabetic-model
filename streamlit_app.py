from typing import Any, Dict, Optional

import requests
import streamlit as st


st.set_page_config(
    page_title="Diabetes Risk Assessment",
    page_icon="DA",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .box {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    .low {
        background: #ecfdf5;
        border-left: 6px solid #10b981;
        padding: 0.9rem;
        border-radius: 10px;
    }
    .medium {
        background: #fffbeb;
        border-left: 6px solid #f59e0b;
        padding: 0.9rem;
        border-radius: 10px;
    }
    .high {
        background: #fef2f2;
        border-left: 6px solid #ef4444;
        padding: 0.9rem;
        border-radius: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def init_state() -> None:
    defaults = {
        "api_base_url": "http://127.0.0.1:8000",
        "access_token": "",
        "current_user": None,
        "profile_id": "",
        "session_id": "",
        "latest_prediction": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


init_state()


def error_message(response: requests.Response) -> str:
    try:
        body = response.json()
    except Exception:
        return response.text or f"HTTP {response.status_code}"

    detail = body.get("detail")
    if isinstance(detail, list):
        return "; ".join(str(item) for item in detail)
    if detail:
        return str(detail)
    return str(body)


def api_request(
    method: str,
    path: str,
    payload: Optional[Dict[str, Any]] = None,
    auth: bool = False,
    timeout: int = 20,
) -> requests.Response:
    headers: Dict[str, str] = {}
    if auth and st.session_state.access_token:
        headers["Authorization"] = f"Bearer {st.session_state.access_token}"

    return requests.request(
        method=method,
        url=f"{st.session_state.api_base_url}{path}",
        json=payload,
        headers=headers,
        timeout=timeout,
    )


def load_current_user() -> None:
    if not st.session_state.access_token:
        st.session_state.current_user = None
        return

    response = api_request("GET", "/auth/me", auth=True)
    if response.status_code == 200:
        st.session_state.current_user = response.json()
        return

    st.session_state.current_user = None


def require_login() -> bool:
    if not st.session_state.access_token:
        st.warning("Please login first in the Authentication page.")
        return False
    return True


st.title("Diabetes Risk Assessment - Streamlit Client")
st.caption("Aligned with FastAPI auth, OTP reset, profile/session workflow, and predictions.")

st.sidebar.markdown("### API Configuration")
st.session_state.api_base_url = st.sidebar.text_input("API Base URL", value=st.session_state.api_base_url)

st.sidebar.markdown("---")
st.sidebar.markdown("### API Health")
try:
    health_resp = api_request("GET", "/health", timeout=5)
    health_resp.raise_for_status()
    health_data = health_resp.json()
    st.sidebar.success("Backend reachable")
    st.sidebar.caption(f"API version: {health_data.get('api_version', 'n/a')}")
    st.sidebar.caption(f"DB connected: {health_data.get('database_connected', False)}")
    st.sidebar.caption(f"Model loaded: {health_data.get('model_loaded', False)}")
except Exception as exc:
    st.sidebar.error(f"Backend unreachable: {exc}")

st.sidebar.markdown("---")
st.sidebar.markdown("### Session State")
st.sidebar.write(f"Logged in: {'yes' if st.session_state.access_token else 'no'}")
st.sidebar.write(f"Profile ID: {st.session_state.profile_id or 'none'}")
st.sidebar.write(f"Session ID: {st.session_state.session_id or 'none'}")


page = st.sidebar.radio(
    "Workflow",
    [
        "Authentication",
        "Profile & Session",
        "Daily Logs",
        "Complete & Predict",
        "Notifications",
    ],
)


if page == "Authentication":
    st.subheader("Authentication and Password Reset (OTP)")

    login_tab, register_tab, reset_tab = st.tabs(["Login", "Register", "Password Reset OTP"])

    with login_tab:
        with st.form("login_form"):
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Password", type="password", key="login_password")
            submit_login = st.form_submit_button("Login")

        if submit_login:
            resp = api_request("POST", "/auth/login", {"email": email, "password": password})
            if resp.status_code == 200:
                token_data = resp.json()
                st.session_state.access_token = token_data.get("access_token", "")
                load_current_user()
                st.success("Logged in successfully.")
            else:
                st.error(f"Login failed: {error_message(resp)}")

        if st.session_state.access_token:
            st.info("You are authenticated.")
            if st.button("Load Current User"):
                load_current_user()
            if st.session_state.current_user:
                st.json(st.session_state.current_user)

            if st.button("Logout"):
                resp = api_request("POST", "/auth/logout", auth=True)
                if resp.status_code in (200, 401):
                    st.session_state.access_token = ""
                    st.session_state.current_user = None
                    st.session_state.profile_id = ""
                    st.session_state.session_id = ""
                    st.success("Logged out.")
                else:
                    st.error(f"Logout failed: {error_message(resp)}")

    with register_tab:
        with st.form("register_form"):
            full_name = st.text_input("Full name", key="register_name")
            reg_email = st.text_input("Email", key="register_email")
            reg_password = st.text_input("Password", type="password", key="register_password")
            submit_register = st.form_submit_button("Create Account")

        if submit_register:
            payload = {
                "email": reg_email,
                "password": reg_password,
                "full_name": full_name or None,
            }
            resp = api_request("POST", "/auth/register", payload)
            if resp.status_code == 200:
                st.success("Account created successfully.")
                st.json(resp.json())
            else:
                st.error(f"Registration failed: {error_message(resp)}")

    with reset_tab:
        st.caption("Step 1: request OTP by email -> Step 2: verify OTP -> Step 3: set new password")

        c1, c2, c3 = st.columns(3)

        with c1:
            with st.form("otp_request_form"):
                reset_email = st.text_input("Email", key="reset_email")
                request_otp = st.form_submit_button("1) Request OTP")
            if request_otp:
                resp = api_request("POST", "/auth/password-reset", {"email": reset_email})
                if resp.status_code == 200:
                    st.success(resp.json().get("message", "OTP requested."))
                else:
                    st.error(f"Request failed: {error_message(resp)}")

        with c2:
            with st.form("otp_verify_form"):
                otp_value = st.text_input("OTP code", key="otp_code")
                verify_otp = st.form_submit_button("2) Verify OTP")
            if verify_otp:
                resp = api_request("POST", "/auth/password-reset/verify", {"otp": otp_value})
                if resp.status_code == 200:
                    st.success(resp.json().get("message", "OTP verified."))
                else:
                    st.error(f"Verification failed: {error_message(resp)}")

        with c3:
            with st.form("otp_confirm_form"):
                new_password = st.text_input("New password", type="password", key="new_reset_password")
                confirm_reset = st.form_submit_button("3) Set New Password")
            if confirm_reset:
                resp = api_request("POST", "/auth/password-reset/confirm", {"new_password": new_password})
                if resp.status_code == 200:
                    st.success(resp.json().get("message", "Password reset completed."))
                else:
                    st.error(f"Password reset failed: {error_message(resp)}")


elif page == "Profile & Session":
    st.subheader("Profile and Assessment Session")
    if require_login():
        load_current_user()
        with st.form("profile_form"):
            age = st.number_input("Age", min_value=0, max_value=150, value=35, step=1)
            sex = st.selectbox("Sex", ["male", "female"])
            height_cm = st.number_input("Height (cm)", min_value=100.0, max_value=250.0, value=170.0, step=0.5)
            weight_kg = st.number_input("Weight (kg)", min_value=20.0, max_value=300.0, value=70.0, step=0.5)
            save_profile = st.form_submit_button("Create Profile")

        if save_profile:
            payload = {
                "age": int(age),
                "sex": sex,
                "height_cm": float(height_cm),
                "weight_kg": float(weight_kg),
            }
            resp = api_request("POST", "/profiles", payload, auth=True)
            if resp.status_code == 200:
                profile = resp.json()
                st.session_state.profile_id = profile.get("id", "")
                st.success("Profile created.")
                st.json(profile)
            else:
                st.error(f"Profile creation failed: {error_message(resp)}")

        c1, c2 = st.columns(2)
        with c1:
            if st.button("Load Latest Profile"):
                resp = api_request("GET", "/profiles/latest", auth=True)
                if resp.status_code == 200:
                    profile = resp.json()
                    st.session_state.profile_id = profile.get("id", "")
                    st.success("Latest profile loaded.")
                    st.json(profile)
                else:
                    st.error(f"Could not load latest profile: {error_message(resp)}")

        with c2:
            if st.button("Start New Session", type="primary"):
                if not st.session_state.profile_id:
                    st.error("Load or create a profile first.")
                else:
                    payload = {"profile_id": st.session_state.profile_id, "target_days": 3}
                    resp = api_request("POST", "/sessions", payload, auth=True)
                    if resp.status_code == 200:
                        session_data = resp.json()
                        st.session_state.session_id = session_data.get("id", "")
                        st.success(f"Session started: {st.session_state.session_id}")
                        st.json(session_data)
                    else:
                        st.error(f"Could not start session: {error_message(resp)}")

        if st.button("List My Sessions"):
            resp = api_request("GET", "/sessions", auth=True)
            if resp.status_code == 200:
                st.json(resp.json())
            else:
                st.error(f"Could not load sessions: {error_message(resp)}")


elif page == "Daily Logs":
    st.subheader("Daily Log Submission")
    if require_login():
        if not st.session_state.session_id:
            st.warning("Start or select a session first in Profile & Session.")
        else:
            st.write(f"Current session: {st.session_state.session_id}")

            with st.form("daily_log_form"):
                day_number = st.number_input("Day number", min_value=1, max_value=30, value=1, step=1)
                urination_frequency = st.number_input("Urination frequency", min_value=0, max_value=30, value=6, step=1)
                thirst_frequency = st.number_input("Thirst frequency", min_value=0, max_value=30, value=5, step=1)
                thirst_level = st.slider("Thirst level", min_value=1, max_value=4, value=2)
                fatigue_level = st.slider("Fatigue level", min_value=1, max_value=5, value=2)
                physical_activity = st.checkbox("Physical activity", value=True)
                alcohol_consumption = st.checkbox("Alcohol consumption", value=False)
                smoking = st.checkbox("Smoking", value=False)
                submit_log = st.form_submit_button("Submit Daily Log")

            if submit_log:
                payload = {
                    "day_number": int(day_number),
                    "urination_frequency": int(urination_frequency),
                    "thirst_frequency": int(thirst_frequency),
                    "thirst_level": int(thirst_level),
                    "fatigue_level": int(fatigue_level),
                    "physical_activity": bool(physical_activity),
                    "alcohol_consumption": bool(alcohol_consumption),
                    "smoking": bool(smoking),
                }
                resp = api_request(
                    "POST",
                    f"/sessions/{st.session_state.session_id}/daily-logs",
                    payload,
                    auth=True,
                )
                if resp.status_code == 200:
                    st.success("Daily log submitted.")
                    st.json(resp.json())
                else:
                    st.error(f"Daily log failed: {error_message(resp)}")

            if st.button("View Session Logs"):
                resp = api_request("GET", f"/sessions/{st.session_state.session_id}/daily-logs", auth=True)
                if resp.status_code == 200:
                    st.json(resp.json())
                else:
                    st.error(f"Could not load logs: {error_message(resp)}")


elif page == "Complete & Predict":
    st.subheader("Complete Session and Run Prediction")
    if require_login():
        if not st.session_state.session_id:
            st.warning("Start or select a session first.")
        else:
            st.write(f"Current session: {st.session_state.session_id}")

            c1, c2 = st.columns(2)
            with c1:
                if st.button("Complete Session"):
                    resp = api_request("POST", f"/sessions/{st.session_state.session_id}/complete", auth=True)
                    if resp.status_code == 200:
                        st.success("Session marked as completed.")
                        st.json(resp.json())
                    else:
                        st.error(f"Complete failed: {error_message(resp)}")

            with c2:
                if st.button("Run Prediction", type="primary"):
                    resp = api_request(
                        "POST",
                        f"/predictions/sessions/{st.session_state.session_id}/predict",
                        auth=True,
                    )
                    if resp.status_code == 200:
                        prediction = resp.json()
                        st.session_state.latest_prediction = prediction
                        risk_level = str(prediction.get("risk_level", "")).lower()
                        probability = float(prediction.get("probability", 0.0))
                        css_class = "medium"
                        if risk_level == "low":
                            css_class = "low"
                        elif risk_level == "high":
                            css_class = "high"
                        st.markdown(
                            f"<div class='{css_class}'><strong>Risk Level:</strong> {risk_level.upper()}<br/><strong>Probability:</strong> {probability:.2%}</div>",
                            unsafe_allow_html=True,
                        )
                        st.json(prediction)
                    else:
                        st.error(f"Prediction failed: {error_message(resp)}")

            if st.button("Get Latest Prediction"):
                resp = api_request("GET", "/predictions/latest", auth=True)
                if resp.status_code == 200:
                    st.session_state.latest_prediction = resp.json()
                    st.json(st.session_state.latest_prediction)
                else:
                    st.error(f"Could not get latest prediction: {error_message(resp)}")


elif page == "Notifications":
    st.subheader("Notifications")
    if require_login():
        unread_only = st.checkbox("Unread only", value=False)
        if st.button("Load Notifications"):
            query = "true" if unread_only else "false"
            resp = api_request("GET", f"/notifications?unread_only={query}", auth=True)
            if resp.status_code == 200:
                notifications = resp.json()
                if not notifications:
                    st.info("No notifications.")
                for item in notifications:
                    st.markdown("<div class='box'>", unsafe_allow_html=True)
                    st.write(f"Title: {item.get('title')}")
                    st.write(f"Type: {item.get('notification_type')}")
                    st.write(f"Read: {item.get('is_read')}")
                    st.write(item.get("message"))
                    if not item.get("is_read"):
                        if st.button(f"Mark as read - {item.get('id')}", key=f"mark_{item.get('id')}"):
                            mark_resp = api_request("POST", f"/notifications/{item.get('id')}/read", auth=True)
                            if mark_resp.status_code == 200:
                                st.success("Marked as read.")
                            else:
                                st.error(f"Failed to mark as read: {error_message(mark_resp)}")
                    st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.error(f"Could not load notifications: {error_message(resp)}")
