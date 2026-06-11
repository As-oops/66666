"""
My AI Chatbot
Simple chatbot application using Streamlit and DeepSeek API
"""
import os

import streamlit as st
from openai import OpenAI
from streamlit.errors import StreamlitSecretNotFoundError

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None


if load_dotenv is not None:
    load_dotenv()


DEFAULT_BASE_URL = "https://api.deepseek.com"
DEFAULT_MODEL = "deepseek-chat"
ROLE_PRESETS = {
    "通用助手": "你是一个有帮助的助手。回答清晰、自然、直接。",
    "Python老师": "你是一个严格但友好的 Python 老师。优先提示思路，不直接给完整答案。",
    "英语陪练": "你是一个英语陪练。请用简单英语回答，并在必要时附一行中文解释。",
    "旅行规划师": "你是一个高效的旅行规划师。给出具体、实用、可执行的建议。",
    "吐槽型朋友": "你是一个嘴上毒舌、其实很热心的朋友。语气有趣，但不要冒犯用户。",
}


def get_setting(name: str, default: str = "") -> str:
    try:
        if name in st.secrets:
            return str(st.secrets[name])
    except StreamlitSecretNotFoundError:
        pass
    return os.getenv(name, default)


def ask_ai(
    client: OpenAI,
    model: str,
    messages: list[dict[str, str]],
    system_prompt: str,
    temperature: float,
) -> str:
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": system_prompt}, *messages],
        temperature=temperature,
    )
    return response.choices[0].message.content or ""


st.set_page_config(page_title="AI 星期八", page_icon="🤖", layout="centered")
st.title("🤖 AI 星期八")
st.caption("Step 6: classroom-ready version")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "selected_role" not in st.session_state:
    st.session_state.selected_role = "通用助手"
if "system_prompt" not in st.session_state:
    st.session_state.system_prompt = ROLE_PRESETS[st.session_state.selected_role]
if "last_role" not in st.session_state:
    st.session_state.last_role = st.session_state.selected_role

default_api_key = get_setting("DEEPSEEK_API_KEY") or get_setting("OPENAI_API_KEY")
default_base_url = get_setting("LLM_BASE_URL", DEFAULT_BASE_URL)
default_model = get_setting("LLM_MODEL", DEFAULT_MODEL)

with st.sidebar:
    api_key = st.text_input("API Key", value=default_api_key, type="password")
    base_url = st.text_input("Base URL", value=default_base_url)
    model = st.text_input("Model", value=default_model)
    role = st.selectbox("Role Preset", options=list(ROLE_PRESETS), key="selected_role")
    if role != st.session_state.last_role:
        st.session_state.system_prompt = ROLE_PRESETS[role]
        st.session_state.last_role = role
    system_prompt = st.text_area("System Prompt", key="system_prompt", height=140)
    temperature = st.slider("Temperature", min_value=0.0, max_value=1.5, value=0.7, step=0.1)
    if st.button("Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

user_input = st.chat_input("请输入内容")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    with st.chat_message("assistant"):
        if not api_key:
            reply = "请先在侧边栏输入 API Key，或在环境变量中设置 DEEPSEEK_API_KEY / OPENAI_API_KEY。"
            st.warning(reply)
        else:
            client = OpenAI(api_key=api_key, base_url=base_url)
            with st.spinner("Thinking..."):
                reply = ask_ai(
                    client=client,
                    model=model,
                    messages=st.session_state.messages,
                    system_prompt=system_prompt,
                    temperature=temperature,
                )
            st.write(reply)

    st.session_state.messages.append({"role": "assistant", "content": reply})
