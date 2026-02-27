import streamlit as st
import requests
from datetime import datetime

API_URL = "http://localhost:8000/ask"
CLEAR_URL = "http://localhost:8000/clear"

st.set_page_config(
    page_title="News RAG Chatbot",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:ital,wght@0,300;0,400;0,500;1,300&display=swap');

*, *::before, *::after { box-sizing: border-box; }

html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
    background-color: #0d0d14 !important;
    color: #e8e8f0;
    font-family: 'DM Sans', sans-serif;
}
[data-testid="stAppViewContainer"] {
    background: radial-gradient(ellipse at 20% 0%, #1a1040 0%, #0d0d14 50%) !important;
}

[data-testid="stSidebar"] {
    background: #111118 !important;
    border-right: 1px solid rgba(255,255,255,0.06) !important;
}
[data-testid="stSidebar"] * { color: #c8c8d8 !important; }

/* INPUT BOX - light background so typed text is visible */
[data-testid="stChatInput"] {
    border-radius: 14px !important;
    border: 1.5px solid rgba(255,255,255,0.15) !important;
    overflow: hidden !important;
}
[data-testid="stChatInput"] textarea {
    background-color: #f0f0f8 !important;
    color: #111122 !important;
    -webkit-text-fill-color: #111122 !important;
    caret-color: #3c3c8e !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.95rem !important;
    border: none !important;
    box-shadow: none !important;
    border-radius: 0 !important;
}
[data-testid="stChatInput"] textarea::placeholder {
    color: #888 !important;
    -webkit-text-fill-color: #888 !important;
}
[data-testid="stChatInput"]:focus-within {
    border-color: #7ee8a2 !important;
    box-shadow: 0 0 0 3px rgba(126,232,162,0.15) !important;
}

/* CHAT BUBBLES using native st.chat_message */
[data-testid="stChatMessage"] {
    border-radius: 14px !important;
    padding: 14px 18px !important;
    margin-bottom: 10px !important;
}
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
    background: rgba(99,102,241,0.14) !important;
    border: 1px solid rgba(99,102,241,0.22) !important;
}
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
}
[data-testid="stChatMessage"] p {
    color: #e2e2f0 !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.93rem !important;
    line-height: 1.65 !important;
    margin: 0 !important;
}

/* Header */
.header-block {
    padding: 1.8rem 0 1.4rem 0;
    border-bottom: 1px solid rgba(255,255,255,0.07);
    margin-bottom: 1.8rem;
}
.header-tag {
    display: inline-block;
    font-size: 0.7rem; font-weight: 600;
    letter-spacing: 0.15em; text-transform: uppercase;
    color: #7ee8a2;
    background: rgba(126,232,162,0.1);
    border: 1px solid rgba(126,232,162,0.2);
    padding: 4px 12px; border-radius: 20px; margin-bottom: 10px;
}
.header-title {
    font-family: 'Syne', sans-serif;
    font-size: 2.2rem; font-weight: 800;
    color: #ffffff; margin: 0; line-height: 1.15;
}
.header-title span { color: #7ee8a2; }
.header-sub { font-size: 0.88rem; color: #666; margin-top: 6px; }

/* Source pill */
.source-pill {
    display: inline-block; font-size: 0.72rem;
    background: rgba(126,232,162,0.1);
    border: 1px solid rgba(126,232,162,0.25);
    color: #7ee8a2; padding: 3px 10px;
    border-radius: 20px; margin-top: 8px;
}
.msg-time { font-size: 0.68rem; color: #444; margin-top: 4px; text-align: right; }

/* Stat cards */
.stat-card {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 12px; padding: 14px; text-align: center; margin-bottom: 8px;
}
.stat-num { font-family: 'Syne', sans-serif; font-size: 1.8rem; font-weight: 800; color: #7ee8a2; }
.stat-label { font-size: 0.72rem; color: #555; text-transform: uppercase; letter-spacing: 0.08em; margin-top: 2px; }

/* Buttons */
.stButton > button {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.09) !important;
    color: #aaa !important; border-radius: 8px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.83rem !important; transition: all 0.2s !important;
}
.stButton > button:hover {
    background: rgba(126,232,162,0.08) !important;
    border-color: rgba(126,232,162,0.3) !important;
    color: #7ee8a2 !important;
}

.divider {
    height: 1px;
    background: linear-gradient(to right, transparent, rgba(255,255,255,0.06), transparent);
    margin: 18px 0;
}
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.08); border-radius: 4px; }
</style>
""", unsafe_allow_html=True)

# Session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "total_questions" not in st.session_state:
    st.session_state.total_questions = 0
if "sources_seen" not in st.session_state:
    st.session_state.sources_seen = set()
if "pending_query" not in st.session_state:
    st.session_state.pending_query = None

# Sidebar
with st.sidebar:
    st.markdown("### 📰 News RAG Chatbot")
    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
    st.markdown("**How it works**")
    st.markdown("""
<div style='font-size:0.82rem; color:#666; line-height:1.8'>
🔍 NewsAPI fetches articles<br>
✂️ Chunked &amp; embedded<br>
🗄️ Stored in ChromaDB<br>
🤖 Ollama LLM answers from context
</div>""", unsafe_allow_html=True)

    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"<div class='stat-card'><div class='stat-num'>{st.session_state.total_questions}</div><div class='stat-label'>Asked</div></div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div class='stat-card'><div class='stat-num'>{len(st.session_state.sources_seen)}</div><div class='stat-label'>Sources</div></div>", unsafe_allow_html=True)

    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
    st.markdown("**💡 Try asking**")
    for s in ["What is Tesla's latest news?", "Any Tesla recalls recently?", "What did Elon Musk say about Tesla?"]:
        if st.button(s, key=s, use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": s, "time": datetime.now().strftime("%H:%M")})
            st.session_state.total_questions += 1
            st.session_state.pending_query = s
            st.rerun()

    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
    if st.button("🗑️ Clear Chat", use_container_width=True):
        try:
            requests.post(CLEAR_URL, timeout=5)
        except Exception:
            pass
        st.session_state.messages = []
        st.session_state.total_questions = 0
        st.session_state.sources_seen = set()
        st.session_state.pending_query = None
        st.rerun()
    st.markdown("<div style='font-size:0.7rem;color:#333;margin-top:14px;text-align:center'>Ollama · ChromaDB · LangChain</div>", unsafe_allow_html=True)

# Header
st.markdown("""
<div class='header-block'>
    <div class='header-tag'>LIVE · NewsAPI + RAG</div>
    <h1 class='header-title'>News <span>Intelligence</span> Chatbot</h1>
    <p class='header-sub'>Ask anything about the latest Tesla news — answers grounded in real articles.</p>
</div>
""", unsafe_allow_html=True)

# Chat history
if not st.session_state.messages:
    st.markdown("""
<div style='text-align:center;padding:60px 0;'>
    <div style='font-size:2.5rem;margin-bottom:10px'>📰</div>
    <div style='font-family:Syne,sans-serif;font-size:1.05rem;color:#555'>No conversation yet</div>
    <div style='font-size:0.83rem;color:#444;margin-top:6px'>Type a question below to get started</div>
</div>""", unsafe_allow_html=True)
else:
    for msg in st.session_state.messages:
        role = msg["role"]
        content = msg["content"]
        time_str = msg.get("time", "")
        is_ai = role == "assistant"

        source_html = ""
        display_content = content
        if is_ai and "📰 Sources:" in content:
            parts = content.split("\n\n📰 Sources:")
            display_content = parts[0].strip()
            if len(parts) > 1:
                known = [s.strip() for s in parts[1].split(",") if s.strip() and s.strip().lower() != "unknown"]
                if known:
                    source_html = f"<div class='source-pill'>📰 {', '.join(known)}</div>"

        with st.chat_message("assistant" if is_ai else "user"):
            st.markdown(display_content)
            if source_html or time_str:
                st.markdown(
                    f"{source_html}<div class='msg-time'>{time_str}</div>",
                    unsafe_allow_html=True
                )

# Process pending query
if st.session_state.pending_query:
    query = st.session_state.pending_query
    st.session_state.pending_query = None
    now = datetime.now().strftime("%H:%M")

    with st.spinner("🔍 Searching articles and generating answer..."):
        try:
            response = requests.post(API_URL, json={"question": query}, timeout=90)
            if response.status_code == 200:
                answer = response.json().get("answer", "No answer found.")
            else:
                answer = f"⚠️ API Error {response.status_code}: {response.text}"
        except requests.exceptions.ConnectionError:
            answer = "⚠️ Could not connect to backend. Make sure `python app.py` is running on port 8000."
        except requests.exceptions.Timeout:
            answer = "⚠️ Request timed out — try restarting Ollama or asking a shorter question."
        except Exception as e:
            answer = f"⚠️ Unexpected error: {e}"

    if "📰 Sources:" in answer:
        for src in answer.split("📰 Sources:")[-1].split(","):
            s = src.strip()
            if s and s.lower() != "unknown":
                st.session_state.sources_seen.add(s)

    st.session_state.messages.append({"role": "assistant", "content": answer, "time": now})
    st.rerun()

# Input
prompt = st.chat_input("Ask about the latest Tesla news...")
if prompt:
    now = datetime.now().strftime("%H:%M")
    st.session_state.messages.append({"role": "user", "content": prompt, "time": now})
    st.session_state.total_questions += 1
    st.session_state.pending_query = prompt
    st.rerun()