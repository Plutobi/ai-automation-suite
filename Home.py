import streamlit as st

st.set_page_config(
    page_title="AI Automation Suite",
    page_icon="🤖",
    layout="centered"
)

st.markdown("""
<style>
    .block-container { padding-top: 2rem; max-width: 820px; }
    .tool-card {
        border: 1px solid #E5E7EB;
        border-radius: 12px;
        padding: 1.2rem 1.5rem;
        margin-bottom: 1rem;
        transition: border-color 0.2s;
    }
    .tool-card:hover { border-color: #6366F1; }
    .tool-title { font-size: 1.1rem; font-weight: 600; margin-bottom: 0.3rem; }
    .tool-desc  { font-size: 0.9rem; color: #6B7280; }
    .badge {
        display: inline-block;
        background: #EEF2FF;
        color: #4338CA;
        border-radius: 20px;
        padding: 2px 10px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-right: 4px;
    }
</style>
""", unsafe_allow_html=True)

# ── Hero ──────────────────────────────────────────────────────
st.title("🤖 AI Automation Suite")
st.markdown("**my fun project** - Three AI-powered automation tools in one place.")
st.divider()

# ── API Key ───────────────────────────────────────────────────
api_key = ""
if hasattr(st, "secrets"):
    api_key = st.secrets.get("ANTHROPIC_API_KEY", "")

if not api_key:
    with st.sidebar:
        st.header("🔑 Setup")
        key = st.text_input("Anthropic API Key", type="password",
                            help="Get yours at console.anthropic.com")
        if key:
            st.session_state["api_key"] = key
            st.success("Key saved for this session.")
else:
    st.session_state["api_key"] = api_key

# ── Tools grid ────────────────────────────────────────────────
st.markdown("### Available Tools")
st.caption("Navigate using the sidebar on the left.")

tools = [
    {
        "icon": "📄",
        "name": "Document Summarizer",
        "desc": "Upload any PDF, DOCX, or TXT file and get an instant AI summary — bullet points, executive summary, or key takeaways.",
        "tags": ["PDF", "DOCX", "TXT"],
        "page": "Document_Summarizer"
    },
    {
        "icon": "📧",
        "name": "Email Classifier & Drafter",
        "desc": "Paste any email to get an instant category, priority score, sentiment analysis, and a ready-to-send reply draft.",
        "tags": ["Urgent", "Follow-up", "Spam", "Draft Reply"],
        "page": "Email_Classifier"
    },
    {
        "icon": "🌐",
        "name": "Web Data Extractor",
        "desc": "Enter any URL — Claude scrapes the page and extracts structured data (products, articles, contacts, jobs) as a downloadable CSV.",
        "tags": ["Products", "News", "Contacts", "CSV Export"],
        "page": "Web_Extractor"
    },
]

for tool in tools:
    tags_html = "".join([f'<span class="badge">{t}</span>' for t in tool["tags"]])
    st.markdown(f"""
    <div class="tool-card">
        <div class="tool-title">{tool["icon"]} {tool["name"]}</div>
        <div class="tool-desc">{tool["desc"]}</div>
        <div style="margin-top:0.6rem">{tags_html}</div>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# ── Stats ─────────────────────────────────────────────────────
col1, col2, col3 = st.columns(3)
col1.metric("Tools", "3")
col2.metric("File formats", "5")
col3.metric("Powered by", "Claude AI")

st.divider()
st.caption("Send me an email if you want something like this alabioluwatobi2018@gmail.com")
