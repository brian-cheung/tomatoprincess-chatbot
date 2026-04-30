import os
import time
import requests
import streamlit as st
from ollama import Client

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="TomatoPrincess AI",
    page_icon="🍅",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
#MainMenu, footer, header { visibility: hidden; }
.stApp { background: #0f0f11; }

/* ── Fixed nav bar ── */
.nav-bar {
    position: fixed; top: 0; left: 0; right: 0; z-index: 999;
    display: flex; align-items: center; justify-content: space-between;
    padding: 12px 24px;
    background: rgba(15,15,17,0.88);
    backdrop-filter: blur(12px);
    border-bottom: 1px solid rgba(255,255,255,0.07);
}
.nav-brand { font-size: 1.1rem; font-weight: 600; color: #f5f5f5; letter-spacing: -0.3px; }
.nav-badge {
    font-size: 0.7rem; font-weight: 500; padding: 2px 8px; border-radius: 99px;
    background: rgba(220,50,50,0.18); color: #ff6b6b;
    border: 1px solid rgba(220,50,50,0.3);
}

/* ── Chat wrapper ── */
.chat-wrapper { max-width: 760px; margin: 80px auto 140px; padding: 0 16px; }

/* ── Message rows ── */
.msg-row { display: flex; gap: 12px; margin-bottom: 20px; animation: fadeUp 0.25s ease; }
.msg-row.user { flex-direction: row-reverse; }
@keyframes fadeUp {
    from { opacity: 0; transform: translateY(8px); }
    to   { opacity: 1; transform: translateY(0); }
}

.avatar {
    width: 34px; height: 34px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 1rem; flex-shrink: 0; margin-top: 2px;
}
.avatar.bot { background: linear-gradient(135deg,#c0392b,#e74c3c); }
.avatar.usr { background: linear-gradient(135deg,#2c3e50,#4a5568); }

.bubble {
    max-width: 80%; padding: 12px 16px; border-radius: 16px;
    font-size: 0.92rem; line-height: 1.65; color: #e8e8ea;
}
.bubble.bot {
    background: #1e1e24; border: 1px solid rgba(255,255,255,0.07);
    border-top-left-radius: 4px;
}
.bubble.usr {
    background: linear-gradient(135deg,#c0392b,#a93226);
    border-top-right-radius: 4px; color: #fff;
}

.ts { font-size: 0.7rem; color: #555; margin-top: 4px; }
.msg-row.user .ts { text-align: right; }

/* ── Sources card ── */
.sources-card {
    margin-top: 8px; padding: 10px 14px;
    background: #16161c; border: 1px solid #252530;
    border-radius: 10px; font-size: 0.8rem; color: #888;
}
.sources-card a { color: #e05252; text-decoration: none; }
.sources-card a:hover { text-decoration: underline; }

/* ── Fixed input bar ── */
.stChatInputContainer, div[data-testid="stChatInput"] {
    position: fixed !important; bottom: 0; left: 50%; transform: translateX(-50%);
    width: min(760px, 100%); padding: 16px;
    background: rgba(15,15,17,0.92); backdrop-filter: blur(16px);
    border-top: 1px solid rgba(255,255,255,0.06); z-index: 998;
}
div[data-testid="stChatInput"] textarea {
    background: #1a1a22 !important; border: 1px solid #2e2e3a !important;
    border-radius: 12px !important; color: #e8e8ea !important;
    font-size: 0.92rem !important; resize: none !important; padding: 12px 16px !important;
}
div[data-testid="stChatInput"] textarea:focus {
    border-color: #c0392b !important;
    box-shadow: 0 0 0 3px rgba(192,57,43,0.15) !important;
}

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background: #13131a !important;
    border-right: 1px solid rgba(255,255,255,0.06) !important;
}
.sb-section {
    font-size: 0.7rem; font-weight: 600; letter-spacing: 0.08em;
    text-transform: uppercase; color: #555; margin: 20px 0 8px;
}
.info-chip {
    display: flex; align-items: center; justify-content: space-between;
    padding: 6px 10px; border-radius: 8px;
    background: #1c1c24; border: 1px solid #2a2a35;
    font-size: 0.78rem; color: #888; margin-bottom: 6px;
}
.info-chip span.val { color: #bbb; font-weight: 500; }
.info-chip .ok  { color: #27ae60; }
.info-chip .bad { color: #e74c3c; }

/* ── Empty / welcome state ── */
.empty-state { text-align: center; padding: 60px 24px; color: #444; }
.empty-state h2 { font-size: 1.6rem; color: #666; margin-bottom: 8px; }
.empty-state p  { font-size: 0.9rem; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #2a2a38; border-radius: 4px; }
</style>
""", unsafe_allow_html=True)

# ── Config ────────────────────────────────────────────────────────────────────
OLLAMA_HOST = st.secrets.get(
    "OLLAMA_HOST",
    "https://suburban-stable-matching-workshops.trycloudflare.com",
)
OLLAMA_API_KEY = st.secrets.get("OLLAMA_API_KEY", "")
if OLLAMA_API_KEY:
    os.environ["OLLAMA_API_KEY"] = OLLAMA_API_KEY

headers = {"Authorization": f"Bearer {OLLAMA_API_KEY}"} if OLLAMA_API_KEY else {}
client = Client(host=OLLAMA_HOST, headers=headers)

# ── Session state ─────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []  # each: {role, content, ts, sources?}

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Settings")

    st.markdown('<div class="sb-section">Model</div>', unsafe_allow_html=True)
    model_name = st.text_input("Model name", value="qwen3:4b", label_visibility="collapsed")

    st.markdown('<div class="sb-section">Behaviour</div>', unsafe_allow_html=True)
    temperature = st.slider("Temperature", 0.0, 1.5, 0.7, 0.1,
                            help="Higher = more creative · Lower = more precise")
    use_web = st.toggle("🌐 Live web search", value=True,
                        help="Augments every reply with real-time search results")

    st.markdown('<div class="sb-section">Connection</div>', unsafe_allow_html=True)
    api_ok = bool(OLLAMA_API_KEY)
    env_ok = bool(os.environ.get("OLLAMA_API_KEY"))
    host_short = OLLAMA_HOST.replace("https://", "").split(".")[0] + "…"
    st.markdown(f"""
    <div class="info-chip">Host <span class="val">{host_short}</span></div>
    <div class="info-chip">API secret
        <span class="{'ok' if api_ok else 'bad'} val">{'✓ set' if api_ok else '✗ missing'}</span>
    </div>
    <div class="info-chip">Env key
        <span class="{'ok' if env_ok else 'bad'} val">{'✓ set' if env_ok else '✗ missing'}</span>
    </div>
    """, unsafe_allow_html=True)

    st.divider()
    if st.button("🗑️  Clear conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    st.caption("TomatoPrincess AI · powered by Ollama")

# ── Nav bar ───────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="nav-bar">
    <div class="nav-brand">🍅 TomatoPrincess AI</div>
    <span class="nav-badge">{'🌐 Web on' if use_web else '📴 Web off'}</span>
</div>
""", unsafe_allow_html=True)

# ── Helper functions ──────────────────────────────────────────────────────────
def do_web_search(query: str, max_results: int = 5) -> dict:
    if not OLLAMA_API_KEY:
        raise Exception("OLLAMA_API_KEY is missing — web search requires an API key.")
    resp = requests.post(
        "https://ollama.com/api/web_search",
        headers={
            "Authorization": f"Bearer {OLLAMA_API_KEY}",
            "Content-Type": "application/json",
        },
        json={"query": query, "max_results": max_results},
        timeout=30,
    )
    if resp.status_code != 200:
        raise Exception(f"Web search failed ({resp.status_code}): {resp.text}")
    return resp.json()


def build_search_context(results: dict):
    lines, sources = [], []
    for r in results.get("results", [])[:5]:
        title   = r.get("title", "Untitled")
        url     = r.get("url", "")
        content = r.get("content", "")
        lines.append(f"Title: {title}\nURL: {url}\nSnippet: {content}")
        if url:
            sources.append({"title": title, "url": url})
    return "\n\n".join(lines), sources


def ask_model(user_prompt: str, history: list, use_web: bool):
    web_context, sources = "", []
    if use_web:
        results = do_web_search(user_prompt)
        web_context, sources = build_search_context(results)

    system = (
        "You are a helpful, concise assistant. "
        "When web results are provided, use them to answer with current information. "
        "When no results are provided, answer from your own knowledge."
    )
    messages = [{"role": "system", "content": system}]
    for m in history:
        if m["role"] in ("user", "assistant"):
            messages.append({"role": m["role"], "content": m["content"]})
    if web_context:
        messages.append({"role": "system", "content": f"Web search results:\n\n{web_context}"})
    messages.append({"role": "user", "content": user_prompt})

    response = client.chat(
        model=model_name,
        messages=messages,
        options={"temperature": temperature},
    )
    text = getattr(response.message, "content", "") or "No response generated."
    return text, sources


def render_sources(sources: list):
    if not sources:
        return
    deduped = list({s["url"]: s for s in sources}.values())
    links = "".join(
        f'<a href="{s["url"]}" target="_blank">↗ {s["title"]}</a><br>'
        for s in deduped
    )
    st.markdown(
        f'<div class="sources-card"><strong>Sources</strong><br>{links}</div>',
        unsafe_allow_html=True,
    )


def now_ts() -> str:
    return time.strftime("%H:%M")


SUGGESTIONS = [
    "🌍 What's happening in the news today?",
    "📈 Latest AI research highlights",
    "🍅 What produce is in season right now?",
    "💡 Give me a quick productivity tip",
]

# ── Render conversation ───────────────────────────────────────────────────────
st.markdown('<div class="chat-wrapper">', unsafe_allow_html=True)

if not st.session_state.messages:
    # Welcome / empty state
    st.markdown("""
    <div class="empty-state">
        <div style="font-size:3rem;margin-bottom:12px">🍅</div>
        <h2>What can I help with?</h2>
        <p>Ask me anything — or pick a suggestion to get started.</p>
    </div>
    """, unsafe_allow_html=True)

    cols = st.columns(2)
    for i, suggestion in enumerate(SUGGESTIONS):
        if cols[i % 2].button(suggestion, use_container_width=True, key=f"sug_{i}"):
            st.session_state.messages.append(
                {"role": "user", "content": suggestion, "ts": now_ts()}
            )
            st.rerun()

else:
    for msg in st.session_state.messages:
        role    = msg["role"]
        content = msg["content"]
        ts      = msg.get("ts", "")
        sources = msg.get("sources", [])
        is_user = role == "user"

        row_cls    = "msg-row user" if is_user else "msg-row"
        bubble_cls = "bubble usr"  if is_user else "bubble bot"
        avatar_cls = "avatar usr"  if is_user else "avatar bot"
        icon       = "👤" if is_user else "🍅"
        flex_extra = "" if is_user else 'style="flex:1;min-width:0"'

        st.markdown(f"""
        <div class="{row_cls}">
            <div class="{avatar_cls}">{icon}</div>
            <div {flex_extra}>
                <div class="{bubble_cls}">{content}</div>
                <div class="ts">{ts}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if not is_user:
            render_sources(sources)

st.markdown("</div>", unsafe_allow_html=True)

# ── Chat input ────────────────────────────────────────────────────────────────
if prompt := st.chat_input("Message TomatoPrincess…"):
    st.session_state.messages.append({"role": "user", "content": prompt, "ts": now_ts()})

    with st.spinner("Searching the web…" if use_web else "Thinking…"):
        try:
            history = [
                m for m in st.session_state.messages[:-1]
                if m["role"] in ("user", "assistant")
            ]
            response_text, sources = ask_model(prompt, history, use_web)
        except Exception as e:
            response_text = f"⚠️ Error: {e}"
            sources = []

    st.session_state.messages.append({
        "role": "assistant",
        "content": response_text,
        "ts": now_ts(),
        "sources": sources,
    })
    st.rerun()
