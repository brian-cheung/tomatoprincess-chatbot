import os
import streamlit as st
from ollama import chat

st.title("💬 Ollama Chatbot")
st.write(
    "This chatbot uses a local Ollama model to generate responses. "
    "Make sure Ollama is running on your machine and that you have already pulled a model "
    "(for example: `ollama pull qwen3:4b`)."
)

# Optional model picker
default_model = "qwen3:4b"
model_name = st.text_input("Ollama model", value=default_model)

# Optional server check info
ollama_host = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
st.caption(f"Using Ollama at: {ollama_host}")

# Create a session state variable to store chat messages
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display the existing chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

def generate_response():
    stream = chat(
        model=model_name,
        messages=[
            {"role": m["role"], "content": m["content"]}
            for m in st.session_state.messages
        ],
        stream=True,
    )

    for chunk in stream:
        content = chunk["message"]["content"]
        if content:
            yield content

if prompt := st.chat_input("What is up?"):
    # Store and display user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate and stream assistant response
    with st.chat_message("assistant"):
        try:
            response = st.write_stream(generate_response)
        except Exception as e:
            response = f"Error: {str(e)}"
            st.error(response)

    # Save assistant response
    st.session_state.messages.append({"role": "assistant", "content": response})
