import streamlit as st
import anthropic
import requests
from bs4 import BeautifulSoup
import pandas as pd
import json, re, sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from utils.rate_limiter import check_rate_limit, record_request, show_usage

st.set_page_config(page_title="Web Extractor", page_icon="🌐", layout="centered")

st.markdown("""
<style>
    .block-container { padding-top:2rem; max-width:820px; }
    .stButton > button { background:#0F766E; color:white; border:none; border-radius:8px; font-weight:600; width:100%; padding:0.6rem; }
    .stButton > button:hover { background:#0D6B63; color:white; }
</style>
""", unsafe_allow_html=True)

st.title("🌐 Web Data Extractor")
st.caption("Enter any URL — Claude extracts structured data you can download as CSV.")
st.divider()

api_key = st.session_state.get("api_key") or (st.secrets.get("ANTHROPIC_API_KEY","") if hasattr(st,"secrets") else "")

EXTRACT_CONFIGS = {
    "Products / Prices":  {"instruction":"Extract all products/items with prices, ratings, and details.", "fields":["name","price","rating","category","description"]},
    "News Articles":      {"instruction":"Extract all news headlines, authors, dates, and summaries.",   "fields":["headline","author","date","summary","url"]},
    "People / Contacts":  {"instruction":"Extract all people with names, roles, organisations, emails.", "fields":["name","role","organisation","email","phone"]},
    "Job Listings":       {"instruction":"Extract all job listings with title, company, location, salary.","fields":["title","company","location","salary","type"]},
    "Custom":             {"instruction":"",                                                              "fields":["field_1","field_2","field_3","field_4","field_5"]},
}

with st.sidebar:
    st.header("⚙️ Settings")
    extract_type    = st.selectbox("What to extract", list(EXTRACT_CONFIGS.keys()))
    custom_instr    = ""
    if extract_type == "Custom":
        custom_instr = st.text_area("Describe what to extract", placeholder="e.g. Extract all event names, dates, and venues")
    model    = st.selectbox("Model", ["claude-haiku-4-5-20251001","claude-sonnet-4-6"])
    max_chars = st.slider("Max page chars", 5000, 40000, 15000, step=5000)
    st.divider()
    st.markdown("**Sample URLs**")
    st.code("https://books.toscrape.com", language=None)
    st.code("https://news.ycombinator.com", language=None)

def scrape(url):
    hdrs = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    r = requests.get(url, headers=hdrs, timeout=15)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    for t in soup(["script","style","nav","footer","header","aside","noscript"]): t.decompose()
    title = soup.title.string.strip() if soup.title else url
    text  = re.sub(r'\n{3,}', '\n\n', soup.get_text(separator="\n", strip=True))
    return title, text

def extract(text, etype, custom, model):
    cfg  = EXTRACT_CONFIGS[etype]
    instr = custom if etype == "Custom" and custom else cfg["instruction"]
    fields= cfg["fields"]
    prompt = f"""From the web page content below, {instr}
Return ONLY a valid JSON array. Each object must use keys: {fields}. Use null for missing fields.
Web page:
{text}"""
    client = anthropic.Anthropic(api_key=api_key)
    msg = client.messages.create(model=model, max_tokens=4096,
        messages=[{"role":"user","content":prompt}])
    raw = msg.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"): raw = raw[4:]
    m = re.search(r'\[.*\]', raw.strip(), re.DOTALL)
    return json.loads(m.group(0) if m else raw.strip())

url_input = st.text_input("Enter a URL:", placeholder="https://books.toscrape.com")

if url_input and api_key:
    show_usage()
    if st.button("🔍 Scrape & Extract"):
        allowed, msg_err = check_rate_limit()
        if not allowed:
            st.warning(msg_err); st.stop()
        with st.spinner("Fetching page..."):
            try:
                if not url_input.startswith("http"): url_input = "https://" + url_input
                title, page_text = scrape(url_input)
                truncated = page_text[:max_chars]
            except Exception as e:
                st.error(f"Could not fetch the page: {e}"); st.stop()

        st.metric("Page", title[:50]+"..." if len(title)>50 else title)
        st.metric("Characters scraped", f"{len(page_text):,}")

        record_request()
        with st.spinner("Claude is extracting data..."):
            try:
                results = extract(truncated, extract_type, custom_instr, model)
            except Exception as e:
                st.error(f"Extraction failed: {e}"); st.stop()

        if not results:
            st.warning("No data found. Try a different URL or extract type."); st.stop()

        st.divider()
        st.markdown(f"### Extracted: {len(results)} items")
        df = pd.DataFrame(results).fillna("—")
        st.dataframe(df, use_container_width=True, hide_index=True)

        csv = pd.DataFrame(results).to_csv(index=False)
        safe = re.sub(r'[^a-z0-9]','_', title.lower())[:30]
        st.download_button("⬇️ Download CSV", data=csv,
                           file_name=f"{safe}_data.csv", mime="text/csv")

elif url_input and not api_key:
    st.warning("Add your API key on the Home page.")
else:
    st.info("Enter a URL above to get started. Try `books.toscrape.com` with Products/Prices.")

st.divider()
st.caption("← Back to Home · AI Automation Suite · Day 5 Capstone")
