import streamlit as st
import anthropic
import json
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from utils.rate_limiter import check_rate_limit, record_request, show_usage

st.set_page_config(page_title="Email Classifier", page_icon="📧", layout="centered")

st.markdown("""
<style>
    .block-container { padding-top:2rem; max-width:780px; }
    .stButton > button { background:#4F46E5; color:white; border:none; border-radius:8px; font-weight:600; width:100%; padding:0.6rem; }
    .stButton > button:hover { background:#4338CA; color:white; }
    .category-badge { display:inline-block; border-radius:20px; padding:4px 16px; font-size:0.85rem; font-weight:600; margin-bottom:0.5rem; }
    .urgent    { background:#FEE2E2; color:#991B1B; }
    .follow-up { background:#FEF3C7; color:#92400E; }
    .spam      { background:#F3F4F6; color:#374151; }
    .normal    { background:#DBEAFE; color:#1E40AF; }
    .info      { background:#D1FAE5; color:#065F46; }
</style>
""", unsafe_allow_html=True)

st.title("📧 Email Classifier & Drafter")
st.caption("Paste any email — get category, priority, sentiment, and a ready-to-send reply.")
st.divider()

api_key = st.session_state.get("api_key") or (st.secrets.get("ANTHROPIC_API_KEY","") if hasattr(st,"secrets") else "")

SAMPLES = {
    "Select a sample...": "",
    "Urgent client issue": "From: sarah@client.com\nSubject: URGENT - System down\n\nOur production system has been down for 2 hours. We're losing thousands per minute. Call me at +1-555-0123 NOW.\n\nSarah, CTO",
    "Meeting follow-up": "From: mark@partner.io\nSubject: Following up on yesterday\n\nHey, just wanted to follow up on our Q3 proposal. Have you reviewed the terms? Let me know if you need clarifications.\n\nMark",
    "Spam": "From: noreply@deals.biz\nSubject: YOU WON $5000!!!\n\nCONGRATULATIONS! Claim your prize NOW before it expires!!!"
}

BADGE_MAP = {"Urgent":"urgent","Follow-up":"follow-up","Spam":"spam","Normal":"normal","Informational":"info"}
PRIORITY_ICON = {"High":"🔴","Medium":"🟡","Low":"🟢"}

with st.sidebar:
    st.header("⚙️ Settings")
    tone      = st.selectbox("Reply Tone", ["Professional","Friendly","Concise","Formal"])
    your_name = st.text_input("Your Name", placeholder="e.g. Tobi")
    your_role = st.text_input("Your Role", placeholder="e.g. Data Scientist")
    model     = st.selectbox("Model", ["claude-haiku-4-5-20251001","claude-sonnet-4-6"])

sample = st.selectbox("Try a sample:", list(SAMPLES.keys()))
email_input = st.text_area("Paste email here:", value=SAMPLES[sample], height=200,
                            placeholder="Paste full email including subject and sender...")

if email_input.strip() and api_key:
    show_usage()
    if st.button("✨ Analyse & Draft Reply"):
        allowed, msg_err = check_rate_limit()
        if not allowed:
            st.warning(msg_err)
            st.stop()
        with st.spinner("Claude is reading your email..."):
            record_request()
            client = anthropic.Anthropic(api_key=api_key)
            sign = your_name or "Me"
            role_line = f"\nMy role: {your_role}" if your_role else ""
            prompt = f"""Analyse the email and return ONLY valid JSON with this exact structure:
{{"category":"one of [Urgent,Follow-up,Normal,Informational,Spam]","priority":"one of [High,Medium,Low]","summary":"one sentence","key_points":["p1","p2","p3"],"sentiment":"one of [Positive,Neutral,Negative,Hostile]","reply_needed":true or false,"draft_reply":"full reply signed as {sign}{role_line} in {tone} tone, or empty string if no reply needed"}}

Email:
{email_input[:8000]}"""
            try:
                msg = client.messages.create(model=model, max_tokens=1024,
                    messages=[{"role":"user","content":prompt}])
                raw = msg.content[0].text.strip()
                if raw.startswith("```"):
                    raw = raw.split("```")[1]
                    if raw.startswith("json"): raw = raw[4:]
                data = json.loads(raw.strip())

                st.divider()
                st.markdown("### Analysis")
                c1,c2,c3 = st.columns(3)
                cat  = data.get("category","Normal")
                pri  = data.get("priority","Medium")
                sent = data.get("sentiment","Neutral")
                c1.markdown(f'<div class="category-badge {BADGE_MAP.get(cat,"normal")}">{cat}</div><br><small style="color:#6B7280">Category</small>', unsafe_allow_html=True)
                c2.markdown(f'<div style="font-size:1.5rem">{PRIORITY_ICON.get(pri,"🟡")}</div><small style="color:#6B7280">Priority: {pri}</small>', unsafe_allow_html=True)
                c3.markdown(f'<div style="font-weight:500;padding-top:4px">{sent}</div><small style="color:#6B7280">Sentiment</small>', unsafe_allow_html=True)

                st.info(f"**Summary:** {data.get('summary','')}")
                pts = data.get("key_points",[])
                if pts:
                    st.markdown("**Key Points**")
                    for p in pts: st.markdown(f"- {p}")

                draft = data.get("draft_reply","")
                if draft and data.get("reply_needed",False):
                    st.divider()
                    st.markdown("### Draft Reply")
                    st.text_area("", value=draft, height=250, label_visibility="collapsed")
                    st.download_button("⬇️ Download Reply", data=draft,
                                       file_name="reply.txt", mime="text/plain")
                elif not data.get("reply_needed",True):
                    st.info("No reply needed.")
            except Exception as e:
                st.error(f"Something went wrong: {e}")
elif email_input.strip() and not api_key:
    st.warning("Add your API key on the Home page.")
else:
    st.info("Paste an email above to get started.")

st.divider()
st.caption("← Back to Home · AI Automation Suite · Day 5 Capstone")
