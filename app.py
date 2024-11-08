import streamlit as st
import time
from typing import Generator
from groq import Groq
import os
from dotenv import load_dotenv
load_dotenv()
st.set_page_config(page_icon="🤖", layout="wide", page_title="Test Prompting for Various LLM Models")

def icon(emoji: str):
    """Shows an emoji as a Notion-style page icon."""
    st.write(
        f'<span style="font-size: 78px; line-height: 1">{emoji}</span>',
        unsafe_allow_html=True,
    )

icon("🤖")

st.subheader("Test and Evaluate Prompts Across Multiple LLM Models", divider="rainbow", anchor=False)





client = Groq(api_key= st.secrets["GROQ_API_KEY"])
 
if "messages" not in st.session_state:
    st.session_state.messages = []

if "selected_model" not in st.session_state:
    st.session_state.selected_model = None


models = {
    "gemma-7b-it": {"name": "Gemma-7b-it", "tokens": 8192, "developer": "Google"},
    "llama3-70b-8192": {"name": "LLaMA3-70b-8192", "tokens": 8192, "developer": "Meta"},
    "llama3-8b-8192": {"name": "LLaMA3-8b-8192", "tokens": 8192, "developer": "Meta"},
    "mixtral-8x7b-32768": {"name": "Mixtral-8x7b-Instruct-v0.1", "tokens": 32768, "developer": "Mistral"},
}


col1, col2 = st.columns(2)

with col1:
    model_option = st.selectbox(
        "Select a model:",
        options=list(models.keys()),
        format_func=lambda x: models[x]["name"],
        index=3  
    )

if st.session_state.selected_model != model_option:
    st.session_state.messages = []
    st.session_state.selected_model = model_option

max_tokens_range = models[model_option]["tokens"]

with col2:
    
    max_tokens = st.slider(
        "Max Tokens:",
        min_value=512, 
        max_value=max_tokens_range,
    
        value=min(32768, max_tokens_range),
        step=512,
        help=f"Adjust the maximum number of tokens (words) for the model's response. Max for selected model: {max_tokens_range}"
    )


for message in st.session_state.messages:
    avatar = '🤖' if message["role"] == "assistant" else '👨‍💻'
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

def generate_chat_responses(chat_completion) -> Generator[str, None, None]:
    """Yield chat response content from the Groq API response."""
    for chunk in chat_completion:
        if chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content

if prompt := st.chat_input("Enter your prompt here..."):
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user", avatar='👨‍💻'):
        st.markdown(prompt)

     
    start_time = time.time()

     
    try:
        chat_completion = client.chat.completions.create(
            model=model_option,
            messages=[{
                "role": m["role"],
                "content": m["content"]
            } for m in st.session_state.messages],
            max_tokens=max_tokens,
            stream=True
        )

         
        with st.chat_message("assistant", avatar="🤖"):
            chat_responses_generator = generate_chat_responses(chat_completion)
            full_response = st.write_stream(chat_responses_generator)

       
        elapsed_time = time.time() - start_time

        
        st.markdown(f"Response Time: {elapsed_time:.2f} seconds")

    except Exception as e:
        st.error(e, icon="🚨")

     
    if isinstance(full_response, str):
        st.session_state.messages.append(
            {"role": "assistant", "content": full_response})
    else:
        
        combined_response = "\n".join(str(item) for item in full_response)
        st.session_state.messages.append(
            {"role": "assistant", "content": combined_response})

    
    with st.expander("Evaluate Correctness"):
        correctness = st.radio("Was the response correct?", ["👍 Yes", "👎 No"], index=0)
        if correctness == "👎 No":
            st.text_area("What was wrong?", placeholder="Provide feedback on the response.")

     
    cost_per_token = 0.0001
    num_tokens = sum(len(m["content"].split()) for m in st.session_state.messages)
    estimated_cost = num_tokens * cost_per_token

    st.markdown(f"Estimated Cost: ${estimated_cost:.4f}")
