import streamlit as st
from ollama import Client, web_search, web_fetch

st.set_page_config(
    page_title="TomatoPrincess Chatbot",
    page_icon="🍅",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.title("🍅 TomatoPrincess Chatbot")
st.write(
    "This chatbot uses Ollama and can use live web search when needed."
)

OLLAMA_HOST = st.secrets.get(
    "OLLAMA_HOST",
    "https://suburban-stable-matching-workshops.trycloudflare.com"
)
OLLAMA_API_KEY = st.secrets.get("OLLAMA_API_KEY", "")

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
    st.caption(f"API key loaded: {'Yes' if OLLAMA_API_KEY else 'No'}")

    if st.button("Clear chat"):
        st.session_state.messages = []
        st.rerun()

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hi, I’m your Ollama chatbot. Ask me anything."}
    ]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

def run_agent(messages, model_name, temperature, use_web):
    available_tools = {
        "web_search": web_search,
        "web_fetch": web_fetch,
    }

    tools = [web_search, web_fetch] if use_web else None
    working_messages = messages.copy()

    for _ in range(6):
        response = client.chat(
            model=model_name,
            messages=working_messages,
            tools=tools,
            options={"temperature": temperature},
        )

        if response.message.content:
            assistant_content = response.message.content
        else:
            assistant_content = ""

        working_messages.append({
            "role": "assistant",
            "content": assistant_content
        })

        tool_calls = getattr(response.message, "tool_calls", None)

        if tool_calls:
            for tool_call in tool_calls:
                tool_name = tool_call.function.name
                tool_args = tool_call.function.arguments or {}

                if tool_name in available_tools:
                    result = available_tools[tool_name](**tool_args)
                    working_messages.append({
                        "role": "tool",
                        "content": str(result)[:8000],
                        "tool_name": tool_name
                    })
                else:
                    working_messages.append({
                        "role": "tool",
                        "content": f"Tool {tool_name} not found.",
                        "tool_name": tool_name
                    })
        else:
            return assistant_content or "No response generated."

    return "I could not complete the request."

if prompt := st.chat_input("Type your message here..."):
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            response = run_agent(
                messages=[
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages
                    if m["role"] in ["user", "assistant"]
                ],
                model_name=model_name,
                temperature=temperature,
                use_web=use_web
            )
            st.markdown(response)
        except Exception as e:
            response = f"Error: {str(e)}"
            st.error(response)

    st.session_state.messages.append({"role": "assistant", "content": response})
