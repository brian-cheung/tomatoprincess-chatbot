import os
import time
import html
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

*, html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    box-sizing: border-box;
}
#MainMenu, footer, header { visibility: hidden; }
.stApp { background: #0d0d0f; }

/* ── Block container ── */
.main .block-container {
    padding-top: 64px !important;
    padding-bottom: 130px !important;
    max-width: 680px !important;
    padding-left: 20px !important;
    padding-right: 20px !important;
}

/* ── Nav ── */
.nav-bar {
    position: fixed; top: 0; left: 0; right: 0; z-index: 999;
    display: flex; align-items: center; justify-content: space-between;
    padding: 0 24px;
    height: 48px;
    background: rgba(13,13,15,0.95);
    backdrop-filter: blur(16px);
    border-bottom: 1px solid rgba(255,255,255,0.05);
}
.nav-brand {
    font-size: 0.8rem; font-weight: 600; color: #d0d0d0;
    letter-spacing: 0.01em; display: flex; align-items: center; gap: 6px;
}
.nav-dot {
    width: 6px; height: 6px; border-radius: 50%;
    background: #c0392b; display: inline-block;
}
.nav-badge {
    font-size: 0.65rem; font-weight: 500; padding: 2px 7px; border-radius: 99px;
    background: rgba(255,255,255,0.05); color: #666;
    border: 1px solid rgba(255,255,255,0.08);
    letter-spacing: 0.02em;
}

/* ── Messages ── */
.msg-row {
    display: flex; gap: 10px; margin-bottom: 16px;
    animation: fadeUp 0.2s ease;
}
.msg-row.user { flex-direction: row-reverse; }
@keyframes fadeUp {
    from { opacity: 0; transform: translateY(6px); }
    to   { opacity: 1; transform: translateY(0); }
}

.avatar {
    width: 26px; height: 26px; border-radius: 50%; flex-shrink: 0;
    display: flex; align-items: center; justify-content: center;
    font-size: 0.58rem; font-weight: 600; margin-top: 1px;
    letter-spacing: 0.04em; text-transform: uppercase;
}
.avatar.bot { background: #1e1e24; color: #c0392b; border: 1px solid #2a2a32; }
.avatar.usr { background: #1e1e24; color: #555; border: 1px solid #2a2a32; }

.bubble {
    max-width: 82%; padding: 9px 13px; border-radius: 14px;
    font-size: 0.8rem; line-height: 1.6; color: #c8c8cc;
    word-break: break-word;
    white-space: pre-wrap;
}
.bubble.bot {
    background: #141418;
    border: 1px solid rgba(255,255,255,0.06);
    border-top-left-radius: 3px;
    color: #c0c0c6;
}
.bubble.usr {
    background: #1a1a20;
    border: 1px solid rgba(255,255,255,0.07);
    border-top-right-radius: 3px;
    color: #a8a8b0;
}

.ts {
    font-size: 0.62rem; color: #3a3a42; margin-top: 3px;
    letter-spacing: 0.02em;
}
.msg-row.user .ts { text-align: right; }

/* ── Sources ── */
.sources-card {
    margin-top: 6px; margin-left: 36px;
    padding: 8px 12px;
    background: transparent;
    border: 1px solid #1e1e26;
    border-radius: 8px;
    font-size: 0.72rem; color: #555;
}
.sources-card .src-label {
    font-size: 0.6rem; text-transform: uppercase; letter-spacing: 0.08em;
    color: #3a3a44; margin-bottom: 5px; font-weight: 600;
}
.sources-card a { color: #6a6a80; text-decoration: none; display: block; margin-bottom: 3px; }
.sources-card a:hover { color: #c0392b; }

/* ── Input bar ── */
div[data-testid="stChatInput"] {
    position: fixed !important;
    bottom: 0 !important;
    left: 50% !important;
    transform: translateX(-50%) !important;
    width: min(680px, 100vw) !important;
    padding: 10px 20px 16px !important;
    background: rgba(13,13,15,0.97) !important;
    backdrop-filter: blur(24px) !important;
    border-top: 1px solid rgba(255,255,255,0.05) !important;
    z-index: 998 !important;
}
div[data-testid="stChatInput"] textarea {
    background: #111115 !important;
    border: 1px solid #222228 !important;
    border-radius: 10px !important;
    color: #c0c0c8 !important;
    font-size: 0.8rem !important;
    font-family: 'Inter', sans-serif !important;
    resize: none !important;
    padding: 10px 44px 10px 14px !important;
    line-height: 1.5 !important;
    min-height: 42px !important;
}
div[data-testid="stChatInput"] textarea:focus {
    border-color: #2a2a35 !important;
    box-shadow: none !important;
    outline: none !important;
}
div[data-testid="stChatInput"] textarea::placeholder {
    color: #3a3a44 !important;
    font-size: 0.78rem !important;
}

/* ── Spinner ── */
div[data-testid="stSpinner"] {
    position: fixed !important;
    bottom: 88px !important;
    left: 50% !important;
    transform: translateX(-50%) !important;
    width: auto !important;
    z-index: 999 !important;
    pointer-events: none !important;
}
div[data-testid="stSpinner"] > div {
    display: inline-flex !important;
    align-items: center !important;
    gap: 8px !important;
    font-size: 0.72rem !important;
    color: #666 !important;
    background: #111115 !important;
    border: 1px solid #222228 !important;
    padding: 6px 14px !important;
    border-radius: 99px !important;
    backdrop-filter: blur(12px) !important;
    white-space: nowrap !important;
}

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background: #0d0d0f !important;
    border-right: 1px solid rgba(255,255,255,0.05) !important;
}
section[data-testid="stSidebar"] * { font-size: 0.78rem !important; }
.sb-section {
    font-size: 0.6rem !important; font-weight: 600; letter-spacing: 0.1em;
    text-transform: uppercase; color: #3a3a44; margin: 18px 0 6px;
}
.info-chip {
    display: flex; align-items: center; justify-content: space-between;
    padding: 5px 9px; border-radius: 7px;
    background: #111115; border: 1px solid #1e1e26;
    font-size: 0.72rem !important; color: #555; margin-bottom: 5px;
}
.info-chip span.val { color: #888; font-weight: 500; }
.info-chip .ok  { color: #3d9e6a; }
.info-chip .bad { color: #c0392b; }

/* ── Empty state ── */
.empty-state {
    text-align: center; padding: 72px 24px 28px;
}
.empty-state h2 {
    font-size: 1rem; color: #555; margin-bottom: 6px;
    font-weight: 500; letter-spacing: -0.01em;
}
.empty-state p { font-size: 0.75rem; color: #3a3a44; margin-bottom: 0; }

/* ── Suggestion buttons ── */
div[data-testid="stButton"] button {
    background: #111115 !important;
    border: 1px solid #1e1e26 !important;
    border-radius: 8px !important;
    color: #555 !important;
    font-size: 0.74rem !important;
    font-weight: 400 !important;
    padding: 8px 12px !important;
    transition: border-color 0.15s, color 0.15s !important;
}
div[data-testid="stButton"] button:hover {
    border-color: #2e2e3a !important;
    color: #888 !important;
    background: #141418 !important;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 3px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #1e1e26; border-radius: 3px; }
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

# Shared HTTP session for efficiency
@st.cache_resource
def get_http_session():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s

@st.cache_resource
def get_ollama_client(host, api_key):
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
    return Client(host=host, headers=headers)

http = get_http_session()
client = get_ollama_client(OLLAMA_HOST, OLLAMA_API_KEY)

# ── Session state ─────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

if "memory_summary" not in st.session_state:
    st.session_state.memory_summary = ""

if "turn_count" not in st.session_state:
    st.session_state.turn_count = 0

if "last_sources" not in st.session_state:
    st.session_state.last_sources = []

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("**Settings**")

    st.markdown('<div class="sb-section">Model</div>', unsafe_allow_html=True)
    model_name = st.text_input("Model", value="qwen3:4b", label_visibility="collapsed")

    st.markdown('<div class="sb-section">Behaviour</div>', unsafe_allow_html=True)
    temperature = st.slider(
        "Temperature", 0.0, 1.5, 0.7, 0.1,
        help="Higher = more creative · Lower = more precise"
    )
    use_web = st.toggle(
        "Live web search", value=True,
        help="Augments replies with real-time results"
    )

    st.markdown('<div class="sb-section">Connection</div>', unsafe_allow_html=True)
    api_ok = bool(OLLAMA_API_KEY)
    env_ok = bool(os.environ.get("OLLAMA_API_KEY"))
    host_short = OLLAMA_HOST.replace("https://", "").replace("http://", "").split(".")[0] + "…"
    st.markdown(f"""
    <div class="info-chip">Host <span class="val">{host_short}</span></div>
    <div class="info-chip">API secret
        <span class="{'ok' if api_ok else 'bad'} val">{'✓' if api_ok else '✗'}</span>
    </div>
    <div class="info-chip">Env key
        <span class="{'ok' if env_ok else 'bad'} val">{'✓' if env_ok else '✗'}</span>
    </div>
    <div class="info-chip">Turns <span class="val">{st.session_state.turn_count}</span></div>
    """, unsafe_allow_html=True)

    st.divider()
    if st.button("Clear conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.memory_summary = ""
        st.session_state.turn_count = 0
        st.session_state.last_sources = []
        st.rerun()
    st.caption("TomatoPrincess · Ollama")

# ── Nav bar ───────────────────────────────────────────────────────────────────
web_status = "web on" if use_web else "web off"
st.markdown(f"""
<div class="nav-bar">
    <div class="nav-brand">
        <span class="nav-dot"></span>
        TomatoPrincess
    </div>
    <span class="nav-badge">{web_status}</span>
</div>
""", unsafe_allow_html=True)

# ── Helpers ───────────────────────────────────────────────────────────────────
def now_ts():
    return time.strftime("%H:%M")

def safe_html_text(text):
    return html.escape(text).replace("\n", "<br>")

def dedupe_sources(sources):
    seen = set()
    out = []
    for s in sources:
        url = s.get("url", "").strip()
        if url and url not in seen:
            seen.add(url)
            out.append({"title": s.get("title", "Source"), "url": url})
    return out

def do_web_search(query, max_results=5, retries=2, timeout=20):
    if not OLLAMA_API_KEY:
        raise Exception("OLLAMA_API_KEY is missing.")

    last_err = None
    for _ in range(retries + 1):
        try:
            resp = http.post(
                "https://ollama.com/api/web_search",
                headers={"Authorization": f"Bearer {OLLAMA_API_KEY}"},
                json={"query": query, "max_results": max_results},
                timeout=timeout,
            )
            if resp.status_code != 200:
                raise Exception(f"Web search failed ({resp.status_code}): {resp.text[:300]}")
            return resp.json()
        except Exception as e:
            last_err = e
            time.sleep(0.6)
    raise last_err

def build_search_context(results):
    lines = []
    sources = []
    for r in results.get("results", [])[:5]:
        title = r.get("title", "Untitled")
        url = r.get("url", "")
        content = r.get("content", "")[:700]
        lines.append(f"Title: {title}\nURL: {url}\nSnippet: {content}")
        if url:
            sources.append({"title": title, "url": url})
    return "\n\n".join(lines), dedupe_sources(sources)

def get_recent_history(messages, max_pairs=6):
    filtered = [m for m in messages if m["role"] in ("user", "assistant")]
    return filtered[-max_pairs * 2:]

def update_memory_summary():
    recent = get_recent_history(st.session_state.messages, max_pairs=4)
    if not recent:
        return

    convo_text = []
    for m in recent:
        role = "User" if m["role"] == "user" else "Assistant"
        convo_text.append(f"{role}: {m['content']}")
    convo_text = "\n".join(convo_text)

    prompt = f"""
You are maintaining a compact conversation memory.
Update the memory summary using the recent dialogue below.

Existing memory summary:
{st.session_state.memory_summary}

Recent dialogue:
{convo_text}

Instructions:
- Keep only durable, helpful context from this conversation.
- Include user preferences, goals, names, constraints, and unresolved tasks.
- Keep it concise.
- Max 120 words.
- Return only the updated memory summary.
""".strip()

    try:
        response = client.chat(
            model=model_name,
            messages=[{"role": "system", "content": prompt}],
            options={"temperature": 0.2},
        )
        summary = getattr(response.message, "content", "").strip()
        if summary:
            st.session_state.memory_summary = summary[:1200]
    except Exception:
        pass

def ask_model(user_prompt, history, use_web):
    web_context = ""
    sources = []

    if use_web:
        try:
            results = do_web_search(user_prompt, max_results=5)
            web_context, sources = build_search_context(results)
        except Exception as e:
            sources = [{"title": "Web search unavailable", "url": ""}]
            web_context = f"Web search error: {e}"

    system = """
You are TomatoPrincess AI, a helpful, concise assistant.
Use a warm but direct tone.

Rules:
- If web search results are provided, use them for current facts.
- If web search failed or no web results are available, be honest about limits.
- Use conversation memory when relevant.
- Keep answers concise but useful.
- Do not repeat the user's question.
""".strip()

    messages = [{"role": "system", "content": system}]

    if st.session_state.memory_summary:
        messages.append({
            "role": "system",
            "content": f"Conversation memory:\n{st.session_state.memory_summary}"
        })

    recent_history = get_recent_history(history, max_pairs=6)
    for m in recent_history:
        messages.append({"role": m["role"], "content": m["content"]})

    if web_context:
        messages.append({
            "role": "system",
            "content": f"Web search context:\n{web_context}"
        })

    messages.append({"role": "user", "content": user_prompt})

    response = client.chat(
        model=model_name,
        messages=messages,
        options={"temperature": temperature},
    )

    return getattr(response.message, "content", "") or "No response generated.", dedupe_sources(sources)

def render_sources(sources):
    clean_sources = [s for s in sources if s.get("url")]
    if not clean_sources:
        return

    links = "".join(
        f'<a href="{html.escape(s["url"])}" target="_blank" rel="noopener noreferrer">↗ {html.escape(s["title"])}</a>'
        for s in clean_sources
    )
    st.markdown(
        f'<div class="sources-card"><div class="src-label">Sources</div>{links}</div>',
        unsafe_allow_html=True,
    )

SUGGESTIONS = [
    "What's in the news today?",
    "Latest AI research highlights",
    "What produce is in season?",
    "Give me a productivity tip",
]

# ── Conversation ──────────────────────────────────────────────────────────────
if not st.session_state.messages:
    st.markdown("""
    <div class="empty-state">
        <h2>What can I help with?</h2>
        <p>Ask anything, or try a suggestion.</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    for i, s in enumerate(SUGGESTIONS):
        col = col1 if i % 2 == 0 else col2
        if col.button(s, use_container_width=True, key=f"sug_{i}"):
            st.session_state.messages.append({"role": "user", "content": s, "ts": now_ts()})
            st.rerun()
else:
    for msg in st.session_state.messages:
        role = msg["role"]
        content = safe_html_text(msg["content"])
        ts = msg.get("ts", "")
        sources = msg.get("sources", [])
        is_user = role == "user"

        row_cls = "msg-row user" if is_user else "msg-row"
        bubble_cls = "bubble usr" if is_user else "bubble bot"
        avatar_cls = "avatar usr" if is_user else "avatar bot"
        avatar_lbl = "you" if is_user else "ai"
        flex_extra = "" if is_user else 'style="flex:1;min-width:0"'

        st.markdown(f"""
        <div class="{row_cls}">
            <div class="{avatar_cls}">{avatar_lbl}</div>
            <div {flex_extra}>
                <div class="{bubble_cls}">{content}</div>
                <div class="ts">{ts}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if not is_user:
            render_sources(sources)

# ── Spacer ────────────────────────────────────────────────────────────────────
st.markdown("<div style='height:80px'></div>", unsafe_allow_html=True)

# ── Input ─────────────────────────────────────────────────────────────────────
if prompt := st.chat_input("Message…"):
    st.session_state.messages.append({
        "role": "user",
        "content": prompt.strip(),
        "ts": now_ts()
    })

    spinner_text = "Searching…" if use_web else "Thinking…"

    with st.spinner(spinner_text):
        try:
            history = st.session_state.messages[:-1]
            response_text, sources = ask_model(prompt.strip(), history, use_web)
        except Exception as e:
            response_text = f"Error: {e}"
            sources = []

    st.session_state.messages.append({
        "role": "assistant",
        "content": response_text,
        "ts": now_ts(),
        "sources": sources,
    })

    st.session_state.turn_count += 1

    # Update compact memory every 2 turns for efficiency
    if st.session_state.turn_count % 2 == 0:
        update_memory_summary()

    st.rerun()
