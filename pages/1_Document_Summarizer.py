import streamlit as st
import anthropic
import PyPDF2
import docx
import io
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from utils.rate_limiter import check_rate_limit, record_request, show_usage

st.set_page_config(page_title="Document Summarizer", page_icon="📄", layout="centered")

st.markdown("""
<style>
    .block-container { padding-top: 2rem; max-width: 780px; }
    .stButton > button { background:#7C3AED; color:white; border:none; border-radius:8px; font-weight:600; width:100%; padding:0.6rem; }
    .stButton > button:hover { background:#6D28D9; color:white; }
    .mode-badge { display:inline-block; background:#7C3AED; color:white; border-radius:20px; padding:2px 12px; font-size:0.8rem; font-weight:600; margin-bottom:0.8rem; }
</style>
""", unsafe_allow_html=True)

st.title("📄 Document Summarizer")
st.caption("Upload any document and get an AI-powered summary instantly.")
st.divider()

api_key = st.session_state.get("api_key") or st.secrets.get("ANTHROPIC_API_KEY", "") if hasattr(st, "secrets") else st.session_state.get("api_key", "")

PROMPTS = {
    "🔹 Bullet Points": "Read the document below and produce a clean bullet-point summary with 8-12 bullets. Each bullet is one concise sentence. Start each with a dash (-):\n\n{text}",
    "📋 Executive Summary": "Write a concise 3-4 paragraph executive summary. Professional tone:\n\n{text}",
    "💡 Key Takeaways": "Extract insights using this format:\n\n## Key Takeaways\n1-5 numbered insights\n\n## Action Items\nbullet list\n\n## One-Line Summary\none sentence\n\nDocument:\n{text}"
}

def extract_text(f) -> str:
    ext = f.name.split(".")[-1].lower()
    if ext == "txt":   return f.read().decode("utf-8")
    if ext == "pdf":
        r = PyPDF2.PdfReader(io.BytesIO(f.read()))
        return "".join([p.extract_text() or "" for p in r.pages])
    if ext == "docx":
        d = docx.Document(io.BytesIO(f.read()))
        return "\n".join([p.text for p in d.paragraphs])
    return ""

with st.sidebar:
    st.header("⚙️ Settings")
    mode  = st.radio("Summary Style", list(PROMPTS.keys()))
    model = st.selectbox("Model", ["claude-haiku-4-5-20251001", "claude-sonnet-4-6"])
    max_c = st.slider("Max chars", 5000, 50000, 20000, step=5000)
    st.markdown("**Formats:** `.txt` `.pdf` `.docx`")

uploaded = st.file_uploader("Upload your document", type=["txt","pdf","docx"], label_visibility="collapsed")

if uploaded:
    raw = extract_text(uploaded)
    truncated = raw[:max_c]
    c1, c2, c3 = st.columns(3)
    c1.metric("Characters", f"{len(raw):,}")
    c2.metric("Words (est.)", f"{len(raw.split()):,}")
    c3.metric("Sent to AI", f"{len(truncated):,}")
    st.divider()

    show_usage()
    if not api_key:
        st.warning("Add your API key on the Home page.")
    elif st.button("✨ Summarize Now"):
        allowed, msg_err = check_rate_limit()
        if not allowed:
            st.warning(msg_err)
        else:
            with st.spinner("Claude is reading your document..."):
                client = anthropic.Anthropic(api_key=api_key)
                msg = client.messages.create(
                    model=model, max_tokens=1024,
                    messages=[{"role":"user","content": PROMPTS[mode].format(text=truncated)}]
                )
                result = msg.content[0].text
            record_request()
            st.markdown(f'<div class="mode-badge">{mode}</div>', unsafe_allow_html=True)
            st.text_area("", value=result, height=350, label_visibility="collapsed")
            st.download_button("⬇️ Download Summary", data=result,
                               file_name=f"summary_{uploaded.name}.txt", mime="text/plain")
else:
    st.info("Upload a `.txt`, `.pdf`, or `.docx` file to get started.")

st.divider()
st.caption("← Back to Home · AI Automation Suite · Day 5 Capstone")
