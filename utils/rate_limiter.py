import streamlit as st
import time

MAX_REQUESTS = 10      # max requests per session
COOLDOWN_SEC = 5       # seconds between requests

def init_rate_limiter():
    if "request_count" not in st.session_state:
        st.session_state["request_count"] = 0
    if "last_request_time" not in st.session_state:
        st.session_state["last_request_time"] = 0.0

def check_rate_limit() -> tuple[bool, str]:
    """
    Returns (allowed: bool, message: str).
    Call before every API request.
    """
    init_rate_limiter()

    count     = st.session_state["request_count"]
    last_time = st.session_state["last_request_time"]
    now       = time.time()
    elapsed   = now - last_time

    if count >= MAX_REQUESTS:
        return False, f"Session limit reached ({MAX_REQUESTS} requests max). Please refresh the page to start a new session."

    if elapsed < COOLDOWN_SEC:
        wait = int(COOLDOWN_SEC - elapsed) + 1
        return False, f"Please wait {wait} second(s) before making another request."

    return True, ""

def record_request():
    """Call immediately after a successful API call."""
    init_rate_limiter()
    st.session_state["request_count"] += 1
    st.session_state["last_request_time"] = time.time()

def show_usage():
    """Display a small usage counter."""
    init_rate_limiter()
    used  = st.session_state["request_count"]
    left  = MAX_REQUESTS - used
    color = "#16A34A" if left > 5 else "#D97706" if left > 2 else "#DC2626"
    st.markdown(
        f'<div style="font-size:0.8rem;color:{color};text-align:right;">'
        f'Requests used: {used}/{MAX_REQUESTS}</div>',
        unsafe_allow_html=True
    )
