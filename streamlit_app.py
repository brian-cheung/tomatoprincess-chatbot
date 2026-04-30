import os
import requests
import streamlit as st
from ollama import Client

st.set_page_config(
    page_title="TomatoPrincess Chatbot",
    page_icon="🍅",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.title("🍅 TomatoPrincess Chatbot")
st.write("Chat with Ollama, with optional live web search.")

OLLAMA_HOST = st.secrets.get(
    "OLLAMA_HOST",
    "https://suburban-stable-matching-workshops.trycloudflare.com",
)
OLLAMA_API_KEY = st.secrets.get("OLLAMA_API_KEY", "")

if OLLAMA_API_KEY:
    os.environ["OLLAMA_API_KEY"] = OLLAMA_API_KEY

headers = {}
if OLLAMA_API_KEY:
    headers["Authorization"] = f"Bearer {OLLAMA_API_KEY}"

client = Client(host=OLLAMA_HOST, headers=headers)

with st.sidebar:
    st.header("Settings")
    model_name = st.text_input("Model name", value="qwen3:4b")
    temperature = st.slider("Temperature", 0.0, 1.5, 0.7, 0.1)
    use_web = st.checkbox("Enable web search", value=True)
    st.caption(f"Ollama host: {OLLAMA_HOST}")
    st.caption(f"API key in secrets: {'Yes' if OLLAMA_API_KEY else 'No'}")
    st.caption(f"API key in env: {'Yes' if os.environ.get('OLLAMA_API_KEY') else 'No'}")

    if st.button("Clear chat"):
        st.session_state.messages = [
            {"role": "assistant", "content": "Hi, I’m your Ollama chatbot. Ask me anything."}
        ]
        st.session_state.sources = []
        st.rerun()

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hi, I’m your Ollama chatbot. Ask me anything."}
    ]

if "sources" not in st.session_state:
    st.session_state.sources = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

def do_web_search(query, max_results=5):
    if not OLLAMA_API_KEY:
        raise Exception("OLLAMA_API_KEY is missing.")

    resp = requests.post(
        "https://ollama.com/api/web_search",
        headers={
            "Authorization": f"Bearer {OLLAMA_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "query": query,
            "max_results": max_results,
        },
        timeout=30,
    )

    if resp.status_code != 200:
        raise Exception(f"Web search failed: {resp.status_code} {resp.text}")

    return resp.json()

def build_search_context(results):
    lines = []
    sources = []

    for r in results.get("results", [])[:5]:
        title = r.get("title", "Untitled")
        url = r.get("url", "")
        content = r.get("content", "")
        lines.append(f"Title: {title}\nURL: {url}\nSnippet: {content}\n")
        if url:
            sources.append({"title": title, "url": url})

    return "\n\n".join(lines), sources

def ask_model(user_prompt, history, use_web):
    web_context = ""
    sources = []

    if use_web:
        search_results = do_web_search(user_prompt, max_results=5)
        web_context, sources = build_search_context(search_results)

    system_prompt = """
You are a helpful assistant.
If web search results are provided, use them to answer with current information.
If no search results are provided, answer normally and do not claim to have browsed the web.
Be clear and concise.
""".strip()

    messages = [{"role": "system", "content": system_prompt}]

    for m in history:
        if m["role"] in ["user", "assistant"]:
            messages.append({"role": m["role"], "content": m["content"]})

    if web_context:
        messages.append(
            {
                "role": "system",
                "content": f"Web search results:\n\n{web_context}",
            }
        )

    messages.append({"role": "user", "content": user_prompt})

    response = client.chat(
        model=model_name,
        messages=messages,
        options={"temperature": temperature},
    )

    text = getattr(response.message, "content", "") or "No response generated."
    return text, sources

if prompt := st.chat_input("Type your message here..."):
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            response_text, sources = ask_model(
                user_prompt=prompt,
                history=st.session_state.messages[:-1],
                use_web=use_web,
            )

            st.markdown(response_text)

            if sources:
                with st.expander("Sources used"):
                    seen = set()
                    for s in sources:
                        if s["url"] not in seen:
                            seen.add(s["url"])
                            st.markdown(f"- [{s['title']}]({s['url']})")

        except Exception as e:
            response_text = f"Error: {str(e)}"
            st.error(response_text)

    st.session_state.messages.append({"role": "assistant", "content": response_text})
