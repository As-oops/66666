"""
智能对话Chatbot系统主程序
基于Python Streamlit框架的网页版智能对话应用
"""
import streamlit as st
import time
from datetime import datetime

# 导入自定义模块
from config import config, get_available_models, get_theme_colors
from history_manager import get_conversation_manager
from chat_utils import (
    validate_message, validate_api_key, clean_message, build_messages,
    get_response_generator, format_timestamp, truncate_text
)

# 页面配置
st.set_page_config(
    page_title="智能对话Chatbot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 初始化会话状态
if 'conversation_manager' not in st.session_state:
    st.session_state.conversation_manager = get_conversation_manager()

if 'current_conversation_id' not in st.session_state:
    st.session_state.current_conversation_id = st.session_state.conversation_manager.current_conversation_id

if 'waiting_for_response' not in st.session_state:
    st.session_state.waiting_for_response = False

if 'last_user_input' not in st.session_state:
    st.session_state.last_user_input = ""

# 加载主题颜色
theme = config.get("theme", "light")
colors = get_theme_colors(theme)

# 加载自定义CSS
st.markdown(f"""
<style>
    /* 全局样式 */
    .stApp {{
        background-color: {colors['background']};
        color: {colors['text']};
    }}
    
    /* 隐藏顶部导航栏 */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}
    
    /* 消息气泡样式 */
    .user-message {{
        background-color: {colors['user_bubble']};
        padding: 12px 16px;
        border-radius: 18px 18px 4px 18px;
        margin: 8px 0;
        max-width: 80%;
        margin-left: auto;
        box-shadow: 0 1px 2px rgba(0,0,0,0.1);
    }}
    
    .assistant-message {{
        background-color: {colors['assistant_bubble']};
        border: 1px solid {colors['border']};
        padding: 12px 16px;
        border-radius: 18px 18px 18px 4px;
        margin: 8px 0;
        max-width: 80%;
        box-shadow: 0 1px 2px rgba(0,0,0,0.1);
    }}
    
    /* 标题样式 */
    .main-title {{
        font-size: 2.5em;
        font-weight: bold;
        text-align: center;
        color: {colors['primary']};
        margin-bottom: 20px;
    }}
    
    /* 会话列表样式 */
    .conversation-item {{
        padding: 10px;
        border-radius: 8px;
        margin: 4px 0;
        cursor: pointer;
        transition: background-color 0.2s;
    }}
    
    .conversation-item:hover {{
        background-color: {colors['secondary_background']};
    }}
    
    .conversation-item.active {{
        background-color: {colors['secondary_background']};
        border-left: 3px solid {colors['primary']};
    }}
    
    /* 输入框样式 */
    .stTextInput > div > div > input {{
        border-radius: 24px;
        padding: 12px 20px;
    }}
    
    /* 按钮样式 */
    .stButton > button {{
        border-radius: 24px;
        transition: all 0.2s;
    }}
    
    .stButton > button:hover {{
        transform: scale(1.02);
    }}
    
    /* 侧边栏样式 */
    .css-1d391kg {{
        background-color: {colors['secondary_background']};
    }}
    
    /* 加载动画 */
    .thinking-indicator {{
        display: inline-block;
        animation: pulse 1.5s infinite;
    }}
    
    @keyframes pulse {{
        0%, 100% {{ opacity: 1; }}
        50% {{ opacity: 0.5; }}
    }}
    
    /* 滚动条样式 */
    ::-webkit-scrollbar {{
        width: 8px;
    }}
    
    ::-webkit-scrollbar-track {{
        background: {colors['secondary_background']};
    }}
    
    ::-webkit-scrollbar-thumb {{
        background: {colors['border']};
        border-radius: 4px;
    }}
    
    /* 响应式布局 */
    @media (max-width: 768px) {{
        .user-message, .assistant-message {{
            max-width: 95%;
        }}
    }}
</style>
""", unsafe_allow_html=True)

def render_sidebar():
    """渲染侧边栏配置面板"""
    with st.sidebar:
        st.markdown("## 📝 对话历史")
        
        # 新建会话按钮
        if st.button("➕ 新建对话", use_container_width=True):
            new_id = st.session_state.conversation_manager.create_new_conversation()
            st.session_state.current_conversation_id = new_id
            st.rerun()
        
        # 搜索框
        search_query = st.text_input("🔍 搜索对话", key="search_input")
        
        # 获取会话列表
        if search_query:
            conversations = st.session_state.conversation_manager.search_conversations(search_query)
        else:
            conversations = st.session_state.conversation_manager.conversations
        
        # 渲染会话列表
        if conversations:
            st.markdown("### 会话列表")
            for conv in conversations[:20]:  # 显示前20个
                is_active = conv["id"] == st.session_state.current_conversation_id
                
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    if st.button(
                        f"💬 {truncate_text(conv['title'], 20)}",
                        key=f"conv_{conv['id']}",
                        use_container_width=True,
                        type="primary" if is_active else "secondary"
                    ):
                        st.session_state.current_conversation_id = conv["id"]
                        st.session_state.conversation_manager.set_current_conversation(conv["id"])
                        st.rerun()
                
                with col2:
                    if st.button("🗑️", key=f"del_{conv['id']}"):
                        st.session_state.conversation_manager.delete_conversation(conv["id"])
                        st.session_state.current_conversation_id = st.session_state.conversation_manager.current_conversation_id
                        st.rerun()
        else:
            st.info("暂无对话记录")
        
        st.divider()
        
        # 配置区域
        st.markdown("## ⚙️ 设置")
        
        # 模拟模式开关（默认关闭）
        st.markdown("### 运行模式")
        use_simulation = st.checkbox(
            "使用模拟模式",
            value=config.get("use_simulation", False),
            help="开启后使用模拟响应，无需API密钥即可体验对话功能"
        )
        config.set("use_simulation", use_simulation)
        
        if use_simulation:
            st.info("🎯 当前运行在模拟模式，可体验基本对话功能")
        else:
            st.success("✅ 当前运行在真实API模式")
        
        # API配置区域
        st.markdown("### API配置")
        
        api_type = st.selectbox(
            "API类型",
            ["DeepSeek", "OpenAI", "Anthropic"],
            index=["deepseek", "openai", "anthropic"].index(config.get("api_type", "deepseek"))
        )
        config.set("api_type", api_type.lower())
        
        api_key = st.text_input(
            "API密钥",
            value=config.get("api_key", ""),
            type="password",
            help="输入您的API密钥"
        )
        if api_key != config.get("api_key"):
            config.set("api_key", api_key)
        
        # 模型选择
        st.markdown("### 模型选择")
        models = get_available_models()
        model_options = [m["name"] for m in models]
        selected_model_name = st.selectbox("选择模型", model_options)
        
        selected_model = None
        for m in models:
            if m["name"] == selected_model_name:
                selected_model = m["id"]
                break
        
        if selected_model != config.get("selected_model"):
            config.set("selected_model", selected_model)
        
        # 如果选择本地模型，显示路径输入
        if selected_model == "local-model":
            base_url = st.text_input(
                "本地模型路径",
                value=config.get("local_model_path", ""),
                help="输入本地模型的API地址"
            )
            config.set("local_model_path", base_url)
        else:
            base_url = st.text_input(
                "API基础URL",
                value=config.get("base_url", "https://api.openai.com/v1"),
                help="输入API基础URL"
            )
            config.set("base_url", base_url)
        
        # 参数调节
        st.markdown("### 参数调节")
        
        context_memory_limit = st.slider(
            "上下文记忆数量",
            min_value=0,
            max_value=20,
            value=int(config.get("context_memory_limit", 10)),
            step=1,
            help="保留最近N条历史消息作为上下文，0表示不使用历史记录"
        )
        config.set("context_memory_limit", context_memory_limit)
        
        temperature = st.slider(
            "Temperature (创造性)",
            min_value=0.0,
            max_value=2.0,
            value=float(config.get("temperature", 0.7)),
            step=0.1,
            help="控制输出的随机性"
        )
        config.set("temperature", temperature)
        
        max_tokens = st.slider(
            "Max Tokens (最大长度)",
            min_value=100,
            max_value=4000,
            value=int(config.get("max_tokens", 2000)),
            step=100,
            help="单次回复的最大token数"
        )
        config.set("max_tokens", max_tokens)
        
        top_p = st.slider(
            "Top P (核采样)",
            min_value=0.0,
            max_value=1.0,
            value=float(config.get("top_p", 1.0)),
            step=0.05,
            help="核采样概率"
        )
        config.set("top_p", top_p)
        
        frequency_penalty = st.slider(
            "Frequency Penalty (频率惩罚)",
            min_value=0.0,
            max_value=2.0,
            value=float(config.get("frequency_penalty", 0.0)),
            step=0.1,
            help="减少重复内容"
        )
        config.set("frequency_penalty", frequency_penalty)
        
        presence_penalty = st.slider(
            "Presence Penalty (存在惩罚)",
            min_value=0.0,
            max_value=2.0,
            value=float(config.get("presence_penalty", 0.0)),
            step=0.1,
            help="增加新话题"
        )
        config.set("presence_penalty", presence_penalty)
        
        # 系统提示词
        st.markdown("### 系统提示词")
        system_prompt = st.text_area(
            "设置AI角色",
            value=config.get("system_prompt", "你是星期八，一个友好、有趣的AI助手。请用中文进行回复。"),
            height=100,
            help="设置AI的系统提示词"
        )
        if system_prompt != config.get("system_prompt"):
            config.set("system_prompt", system_prompt)
        
        # 主题切换
        st.markdown("### 界面设置")
        theme_options = ["light", "dark"]
        new_theme = st.selectbox("主题模式", theme_options, index=theme_options.index(theme))
        if new_theme != theme:
            config.set("theme", new_theme)
            st.rerun()
        
        # 保存配置按钮
        if st.button("💾 保存配置", use_container_width=True):
            if config.save_config():
                st.success("配置已保存！")
            else:
                st.error("保存失败！")
        
        st.divider()
        
        # 帮助信息
        st.markdown("### 使用帮助")
        with st.expander("查看使用说明"):
            st.markdown("""
            1. **配置API**: 在侧边栏输入您的API密钥
            2. **选择模型**: 选择要使用的AI模型
            3. **开始对话**: 在下方输入框输入问题
            4. **管理会话**: 左侧可以创建、切换、删除会话
            5. **导出对话**: 支持导出为TXT或Markdown格式
            """)
        
        with st.expander("参数说明"):
            st.markdown("""
            - **Temperature**: 值越低输出越确定，值越高输出越随机
            - **Max Tokens**: 单次回复的最大长度
            - **Top P**: 核采样，影响输出的多样性
            """)

def render_messages():
    """渲染消息列表"""
    messages = st.session_state.conversation_manager.get_messages()
    
    if not messages:
        st.info("👋 开始您的第一次对话吧！")
        return
    
    for msg in messages:
        if msg["role"] == "user":
            with st.chat_message("user"):
                st.markdown(msg["content"])
        else:
            with st.chat_message("assistant"):
                st.markdown(msg["content"])

def handle_user_input(user_input: str):
    """
    处理用户输入
    
    Args:
        user_input: 用户输入的文本
    """
    # 验证输入
    is_valid, error_msg = validate_message(user_input)
    if not is_valid:
        st.error(error_msg)
        return
    
    # 清理输入
    user_input = clean_message(user_input)
    
    # 添加用户消息
    st.session_state.conversation_manager.add_message("user", user_input)
    
    # 显示用户消息
    with st.chat_message("user"):
        st.markdown(user_input)
    
    # 显示助手思考中...
    with st.chat_message("assistant"):
        thinking_placeholder = st.empty()
        thinking_placeholder.markdown("🤔 思考中...")
        
        full_response = []
        response_placeholder = st.empty()
        
        try:
            # 获取所有历史消息（包括刚添加的用户消息）
            all_messages = st.session_state.conversation_manager.get_messages()
            
            # 构建API请求消息（排除最后一条用户消息，因为已经单独添加了）
            history_messages = all_messages[:-1]
            
            # 获取上下文记忆数量配置
            context_memory_limit = config.get("context_memory_limit", 10)
            
            # 限制上下文记忆数量（保留最近的N条消息）
            if len(history_messages) > context_memory_limit:
                history_messages = history_messages[-context_memory_limit:]
            
            # 构建消息列表
            system_prompt = config.get("system_prompt")
            built_messages = build_messages(history_messages, system_prompt)
            
            # 添加当前用户消息
            built_messages.append({
                "role": "user",
                "content": user_input
            })
            
            # 显示上下文记忆信息
            if history_messages:
                context_info = f"📝 已加载 {len(history_messages)} 条历史消息作为上下文"
                thinking_placeholder.markdown(context_info)
            
            # 获取响应生成器
            generator = get_response_generator(
                messages=built_messages,
                model=config.get("selected_model", "gpt-3.5-turbo"),
                api_key=config.get("api_key", ""),
                base_url=config.get("base_url", "https://api.openai.com/v1"),
                params={
                    "temperature": config.get("temperature", 0.7),
                    "max_tokens": config.get("max_tokens", 2000),
                    "top_p": config.get("top_p", 1.0),
                    "frequency_penalty": config.get("frequency_penalty", 0.0),
                    "presence_penalty": config.get("presence_penalty", 0.0),
                    "stream": True
                },
                use_simulation=config.get("use_simulation", False),
                api_type=config.get("api_type", "deepseek")
            )
            
            # 清空思考提示
            thinking_placeholder.empty()
            
            # 流式显示响应
            for chunk in generator:
                if chunk:
                    full_response.append(chunk)
                    response_placeholder.markdown("".join(full_response))
            
            assistant_message = "".join(full_response)
            
            # 添加助手消息到历史
            st.session_state.conversation_manager.add_message("assistant", assistant_message)
            
        except Exception as e:
            error_msg = f"❌ 出错了: {str(e)}"
            thinking_placeholder.markdown(error_msg)
            st.session_state.conversation_manager.add_message("assistant", error_msg)

def render_export_buttons():
    """渲染导出按钮"""
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # 导出为TXT
        txt_content = st.session_state.conversation_manager.export_conversation(format="txt")
        if txt_content:
            st.download_button(
                "📄 导出为TXT",
                txt_content,
                file_name="conversation.txt",
                mime="text/plain",
                use_container_width=True
            )
    
    with col2:
        # 导出为Markdown
        md_content = st.session_state.conversation_manager.export_conversation(format="markdown")
        if md_content:
            st.download_button(
                "📝 导出为Markdown",
                md_content,
                file_name="conversation.md",
                mime="text/markdown",
                use_container_width=True
            )
    
    with col3:
        # 复制对话内容
        messages = st.session_state.conversation_manager.get_messages()
        copy_text = "\n\n".join([f"**{'用户' if m['role']=='user' else '助手'}**: {m['content']}" for m in messages])
        if copy_text:
            st.button(
                "📋 复制对话",
                on_click=lambda: st.clipboard(copy_text),
                use_container_width=True
            )

def render_reset_button():
    """渲染重置按钮"""
    if st.button("🔄 重置当前对话", use_container_width=True):
        if st.session_state.conversation_manager.reset_current_conversation():
            st.success("对话已重置")
            st.rerun()
        else:
            st.error("重置失败")

def main():
    """主函数"""
    # 渲染侧边栏
    render_sidebar()
    
    # 主内容区
    st.markdown('<h1 class="main-title">🌟 星期八 AI 对话助手</h1>', unsafe_allow_html=True)
    
    # 助手介绍卡片
    with st.container():
        col1, col2 = st.columns([1, 3])
        with col1:
            st.markdown("""
            <div style="text-align: center;">
                <div style="font-size: 64px; margin-bottom: 10px;">🤖</div>
                <div style="font-weight: bold; color: #ff4b4b;">星期八</div>
                <div style="font-size: 12px; color: #666;">你的专属AI助手</div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown("""
            👋 你好！我是**星期八**，一个友好、有趣的AI助手。
            
            我可以帮你：
            - 💡 回答各种问题
            - 📝 撰写文章和文案
            - 🤔 提供建议和思路
            - 🎯 解决编程难题
            
            开始我们的对话吧！
            """)
    
    st.divider()
    
    # 渲染消息
    with st.container():
        render_messages()
    
    # 消息输入
    user_input = st.chat_input("输入你想对星期八说的话...", key="chat_input")
    
    if user_input and user_input != st.session_state.last_user_input:
        st.session_state.last_user_input = user_input
        handle_user_input(user_input)
    
    # 底部操作按钮
    st.divider()
    col1, col2 = st.columns(2)
    
    with col1:
        render_export_buttons()
    
    with col2:
        render_reset_button()

if __name__ == "__main__":
    main()
