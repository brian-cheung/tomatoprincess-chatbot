import streamlit as st
from ollama import Client

st.set_page_config(page_title="TomatoPrincess Chatbot", page_icon="🍅", layout="centered")

st.title("🍅 TomatoPrincess Chatbot")
st.write(
    "This chatbot uses Ollama. "
    "It can work with a local Ollama server or a remote Ollama endpoint."
)

# Read secrets safely
OLLAMA_HOST = st.secrets.get("OLLAMA_HOST", "http://127.0.0.1:11434")
OLLAMA_API_KEY = st.secrets.get("OLLAMA_API_KEY", "")

# Build client
headers = {}
if OLLAMA_API_KEY:
    headers["Authorization"] = f"Bearer {OLLAMA_API_KEY}"

client = Client(host=OLLAMA_HOST, headers=headers)

# Sidebar settings
with st.sidebar:
    st.header("Settings")
    model_name = st.text_input("Model name", value="qwen3:4b")
    temperature = st.slider("Temperature", 0.0, 1.5, 0.7, 0.1)
    st.caption(f"Ollama host: {OLLAMA_HOST}")
    st.caption(f"API key loaded: {'Yes' if OLLAMA_API_KEY else 'No'}")

    if st.button("Clear chat"):
        st.session_state.messages = []
        st.rerun()

# Session state for chat history
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Hi, I’m your Ollama chatbot. Ask me anything."
        }
    ]

# Display existing messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

def stream_ollama_response():
    stream = client.chat(
        model=model_name,
        messages=[
            {"role": m["role"], "content": m["content"]}
            for m in st.session_state.messages
        ],
        stream=True,
        options={"temperature": temperature},
    )

    for chunk in stream:
        content = chunk["message"]["content"]
        if content:
            yield content

# Chat input
if prompt := st.chat_input("Type your message here..."):
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            response = st.write_stream(stream_ollama_response)
        except Exception as e:
            response = f"Error: {str(e)}"
            st.error(response)

    st.session_state.messages.append({"role": "assistant", "content": response})
