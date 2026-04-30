import os
import streamlit as st
from ollama import Client, web_search, web_fetch

st.set_page_config(
    page_title="TomatoPrincess Chatbot",
    page_icon="🍅",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.title("🍅 TomatoPrincess Chatbot")
st.write("Chat with a local or remote Ollama model, with optional live web search.")

# -----------------------------
# Secrets / config
# -----------------------------
OLLAMA_HOST = st.secrets.get(
    "OLLAMA_HOST",
    "https://suburban-stable-matching-workshops.trycloudflare.com",
)
OLLAMA_API_KEY = st.secrets.get("OLLAMA_API_KEY", "")

# Important: make the API key available to Ollama web_search/web_fetch helpers
if OLLAMA_API_KEY:
    os.environ["OLLAMA_API_KEY"] = OLLAMA_API_KEY

headers = {}
if OLLAMA_API_KEY:
    headers["Authorization"] = f"Bearer {OLLAMA_API_KEY}"

client = Client(host=OLLAMA_HOST, headers=headers)

# -----------------------------
# Sidebar
# -----------------------------
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
        st.rerun()

# -----------------------------
# Session state
# -----------------------------
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hi, I’m your Ollama chatbot. Ask me anything."}
    ]

if "sources" not in st.session_state:
    st.session_state.sources = []

# -----------------------------
# Render chat history
# -----------------------------
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# -----------------------------
# Agent loop
# -----------------------------
def run_agent(messages, model_name, temperature, use_web=True, max_steps=6):
    available_tools = {
        "web_search": web_search,
        "web_fetch": web_fetch,
    }

    tools = [web_search, web_fetch] if use_web else None
    working_messages = list(messages)
    collected_sources = []

    for _ in range(max_steps):
        response = client.chat(
            model=model_name,
            messages=working_messages,
            tools=tools,
            options={"temperature": temperature},
        )

        assistant_text = getattr(response.message, "content", "") or ""
        tool_calls = getattr(response.message, "tool_calls", None)

        if assistant_text:
            working_messages.append(
                {"role": "assistant", "content": assistant_text}
            )

        if not tool_calls:
            return assistant_text if assistant_text else "No response generated.", collected_sources

        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            tool_args = tool_call.function.arguments or {}

            try:
                if tool_name not in available_tools:
                    tool_result = f"Tool {tool_name} not found."
                else:
                    tool_result = available_tools[tool_name](**tool_args)

                # Keep some source details for display
                if tool_name == "web_search" and isinstance(tool_result, dict):
                    results = tool_result.get("results", [])
                    for r in results[:5]:
                        if isinstance(r, dict):
                            collected_sources.append(
                                {
                                    "title": r.get("title", "Untitled"),
                                    "url": r.get("url", ""),
                                }
                            )

                if tool_name == "web_fetch" and isinstance(tool_args, dict):
                    url = tool_args.get("url", "")
                    if url:
                        collected_sources.append({"title": "Fetched page", "url": url})

                working_messages.append(
                    {
                        "role": "tool",
                        "content": str(tool_result)[:8000],
                        "tool_name": tool_name,
                    }
                )

            except Exception as e:
                working_messages.append(
                    {
                        "role": "tool",
                        "content": f"Tool {tool_name} failed: {str(e)}",
                        "tool_name": tool_name,
                    }
                )

    return "I could not complete the request within the tool limit.", collected_sources

# -----------------------------
# Chat input
# -----------------------------
if prompt := st.chat_input("Type your message here..."):
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            response_text, sources = run_agent(
                messages=[
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages
                    if m["role"] in ["user", "assistant"]
                ],
                model_name=model_name,
                temperature=temperature,
                use_web=use_web,
            )

            st.markdown(response_text)

            if sources:
                unique_sources = []
                seen = set()
                for s in sources:
                    key = s.get("url", "")
                    if key and key not in seen:
                        seen.add(key)
                        unique_sources.append(s)

                with st.expander("Sources used"):
                    for s in unique_sources[:10]:
                        title = s.get("title", "Source")
                        url = s.get("url", "")
                        if url:
                            st.markdown(f"- [{title}]({url})")

        except Exception as e:
            response_text = f"Error: {str(e)}"
            st.error(response_text)

    st.session_state.messages.append({"role": "assistant", "content": response_text})
