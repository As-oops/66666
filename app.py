"""
星期八 AI 对话助手
基于Python Streamlit框架的网页版智能对话应用
支持DeepSeek、OpenAI、Anthropic等多模型接入
"""
import os
import time
import json
from datetime import datetime
from typing import Generator, List, Dict, Any, Optional

import streamlit as st
from openai import OpenAI, AuthenticationError, RateLimitError, APIError
from streamlit.errors import StreamlitSecretNotFoundError

# 尝试导入dotenv
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ============ 配置常量 ============
DEFAULT_BASE_URL = "https://api.deepseek.com"
DEFAULT_MODEL = "deepseek-chat"
MAX_MESSAGE_LENGTH = 4000
DEBOUNCE_INTERVAL = 0.5  # 防抖间隔（秒）

# 角色预设
ROLE_PRESETS = {
    "星期八": "你是星期八，一个友好、有趣的AI助手。请用中文进行回复。你善于倾听、理解用户需求，并提供有帮助的建议。",
    "通用助手": "你是一个有帮助的助手。回答清晰，自然，直接。",
    "Python老师": "你是一个严格但友好的Python老师。优先提示思路，不直接给完整答案。",
    "法语陪练": "你是一个法语陪练。请用简单法语回答，并在必要时附一行中文解释。",
    "旅行规划师": "你是一个高效的旅行规划师。给出具体、实用、可执行的建议。",
    "吐槽型朋友": "你是一个嘴上毒舌、其实很热心的朋友。语气有趣，但不要冒犯用户。",
}

# 主题配置
THEMES = {
    "light": {
        "background": "#ffffff",
        "text": "#1a1a2e",
        "primary": "#4a90d9",
        "secondary": "#f8f9fa",
        "user_bubble": "#dcf8c6",
        "assistant_bubble": "#ffffff",
        "border": "#e0e0e0"
    },
    "dark": {
        "background": "#1a1a2e",
        "text": "#e0e0e0",
        "primary": "#4a90d9",
        "secondary": "#16213e",
        "user_bubble": "#4a90d9",
        "assistant_bubble": "#2d3748",
        "border": "#4a5568"
    }
}


# ============ 工具函数 ============
def get_setting(name: str, default: str = "") -> str:
    """获取配置"""
    try:
        if name in st.secrets:
            return str(st.secrets[name])
    except StreamlitSecretNotFoundError:
        pass
    return os.getenv(name, default)


def validate_message(message: str, max_length: int = MAX_MESSAGE_LENGTH) -> tuple[bool, str]:
    """验证消息格式和长度"""
    if not message or not message.strip():
        return False, "消息不能为空"
    if len(message) > max_length:
        return False, f"消息长度不能超过{max_length}个字符"
    return True, ""


def clean_message(message: str) -> str:
    """清理消息文本"""
    return message.strip()


def truncate_text(text: str, max_length: int = 30) -> str:
    """截断文本"""
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."


def format_timestamp(timestamp: str = None) -> str:
    """格式化时间戳"""
    if not timestamp:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return timestamp


# ============ 会话管理 ============
class ConversationManager:
    """对话会话管理器"""
    
    def __init__(self, storage_file: str = "conversations.json"):
        self.storage_file = storage_file
        self.conversations = self.load_conversations()
        self.current_conversation_id = None
        
        # 如果没有会话，创建一个新的
        if not self.conversations:
            self.create_new_conversation()
    
    def load_conversations(self) -> List[Dict[str, Any]]:
        """从文件加载会话数据"""
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"加载会话失败: {e}")
        return []
    
    def save_conversations(self) -> bool:
        """保存会话数据到文件"""
        try:
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(self.conversations, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存会话失败: {e}")
            return False
    
    def create_new_conversation(self, title: str = None) -> str:
        """创建新会话"""
        import uuid
        conversation_id = str(uuid.uuid4())[:8]
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        conversation = {
            "id": conversation_id,
            "title": title or f"新对话 {timestamp}",
            "created_at": timestamp,
            "updated_at": timestamp,
            "messages": []
        }
        
        self.conversations.insert(0, conversation)
        self.current_conversation_id = conversation_id
        self.save_conversations()
        
        return conversation_id
    
    def get_current_conversation(self) -> Optional[Dict[str, Any]]:
        """获取当前会话"""
        if not self.current_conversation_id:
            return None
        
        for conv in self.conversations:
            if conv["id"] == self.current_conversation_id:
                return conv
        return None
    
    def set_current_conversation(self, conversation_id: str) -> bool:
        """设置当前会话"""
        for conv in self.conversations:
            if conv["id"] == conversation_id:
                self.current_conversation_id = conversation_id
                return True
        return False
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """删除会话"""
        initial_length = len(self.conversations)
        self.conversations = [c for c in self.conversations if c["id"] != conversation_id]
        
        if len(self.conversations) < initial_length:
            if self.current_conversation_id == conversation_id:
                self.current_conversation_id = self.conversations[0]["id"] if self.conversations else None
            
            if not self.conversations:
                self.create_new_conversation()
            
            self.save_conversations()
            return True
        return False
    
    def add_message(self, role: str, content: str) -> bool:
        """添加消息到当前会话"""
        conversation = self.get_current_conversation()
        if not conversation:
            return False
        
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        conversation["messages"].append(message)
        conversation["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 如果是第一条用户消息，更新会话标题
        if role == "user" and len(conversation["messages"]) == 1:
            conversation["title"] = content[:30] + ("..." if len(content) > 30 else "")
        
        self.save_conversations()
        return True
    
    def get_messages(self, conversation_id: str = None) -> List[Dict[str, Any]]:
        """获取会话消息"""
        if conversation_id:
            for conv in self.conversations:
                if conv["id"] == conversation_id:
                    return conv.get("messages", [])
        else:
            conversation = self.get_current_conversation()
            if conversation:
                return conversation.get("messages", [])
        return []
    
    def search_conversations(self, keyword: str) -> List[Dict[str, Any]]:
        """搜索会话"""
        if not keyword:
            return self.conversations
        
        keyword = keyword.lower()
        results = []
        
        for conv in self.conversations:
            if keyword in conv.get("title", "").lower():
                results.append(conv)
                continue
            
            for msg in conv.get("messages", []):
                if keyword in msg["content"].lower():
                    results.append(conv)
                    break
        
        return results
    
    def get_conversations_list(self, page: int = 1, page_size: int = 10) -> Dict[str, Any]:
        """分页获取会话列表"""
        total = len(self.conversations)
        total_pages = (total + page_size - 1) // page_size if total > 0 else 1
        
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        
        return {
            "conversations": self.conversations[start_idx:end_idx],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages
        }
    
    def reset_current_conversation(self) -> bool:
        """重置当前会话"""
        conversation = self.get_current_conversation()
        if conversation:
            conversation["messages"] = []
            conversation["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.save_conversations()
            return True
        return False
    
    def export_conversation(self, format: str = "txt") -> str:
        """导出对话"""
        conversation = self.get_current_conversation()
        if not conversation or not conversation.get("messages"):
            return ""
        
        messages = conversation["messages"]
        
        if format == "txt":
            lines = [f"对话导出 - {conversation['title']}\n"]
            lines.append(f"导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            lines.append("=" * 50 + "\n\n")
            
            for msg in messages:
                role = "用户" if msg["role"] == "user" else "星期八"
                lines.append(f"【{role}】\n{msg['content']}\n\n")
            
            return "".join(lines)
        
        elif format == "markdown":
            lines = [f"# {conversation['title']}\n\n"]
            lines.append(f"**导出时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            lines.append("---\n\n")
            
            for msg in messages:
                role = "用户" if msg["role"] == "user" else "星期八"
                lines.append(f"**{role}**: {msg['content']}\n\n")
            
            return "".join(lines)
        
        return ""


# 获取会话管理器实例
@st.cache_resource
def get_conversation_manager():
    return ConversationManager()


# ============ API调用函数 ============
def validate_api_key(api_key: str) -> bool:
    """验证API密钥格式"""
    if not api_key or not api_key.strip():
        return False
    if len(api_key) < 10:
        return False
    return True


def call_api_stream(
    client: OpenAI,
    model: str,
    messages: List[Dict[str, str]],
    temperature: float,
    max_tokens: int,
    top_p: float,
    stream: bool = True
) -> Generator[str, None, None]:
    """调用API进行流式输出"""
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            stream=stream
        )
        
        if stream:
            for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        else:
            yield response.choices[0].message.content or ""
            
    except AuthenticationError:
        yield "❌ API密钥无效，请检查是否正确配置。"
    except RateLimitError:
        yield "⚠️ API请求频率超限，请稍后再试。"
    except APIError as e:
        yield f"❌ API调用出错: {str(e)}"
    except Exception as e:
        yield f"❌ 发生未知错误: {str(e)}"


def simulate_response(user_message: str) -> Generator[str, None, None]:
    """模拟AI响应"""
    import random
    
    responses = [
        f"我理解你说的「{user_message[:20]}...」。让我想想怎么回答你。",
        "这是个很有趣的问题！让我来帮你分析一下。",
        "根据我的理解，你想知道的是...对吗？",
        "好的，我来帮你解答这个问题。",
    ]
    
    response = random.choice(responses)
    
    for char in response:
        yield char
        time.sleep(0.02)
    
    time.sleep(0.3)
    
    additional = [
        "\n\n有什么其他问题吗？",
        "\n\n希望我的回答对你有帮助！",
        "\n\n需要我进一步解释吗？",
    ]
    
    for char in random.choice(additional):
        yield char
        time.sleep(0.02)


# ============ Streamlit应用 ============
st.set_page_config(
    page_title="🌟 星期八 AI 对话助手",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 初始化session state
if "conversation_manager" not in st.session_state:
    st.session_state.conversation_manager = get_conversation_manager()

if "current_conversation_id" not in st.session_state:
    st.session_state.current_conversation_id = st.session_state.conversation_manager.current_conversation_id

if "last_user_input" not in st.session_state:
    st.session_state.last_user_input = ""

if "debounce_timer" not in st.session_state:
    st.session_state.debounce_timer = 0

if "current_page" not in st.session_state:
    st.session_state.current_page = 1

if "theme" not in st.session_state:
    st.session_state.theme = "light"

if "use_simulation" not in st.session_state:
    st.session_state.use_simulation = False

if "context_memory_limit" not in st.session_state:
    st.session_state.context_memory_limit = 10

# 加载主题
theme = st.session_state.theme
colors = THEMES.get(theme, THEMES["light"])

# 自定义CSS
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
    
    /* 按钮样式 */
    .stButton > button {{
        border-radius: 24px;
        transition: all 0.2s;
    }}
    
    .stButton > button:hover {{
        transform: scale(1.02);
    }}
    
    /* 输入框样式 */
    .stTextInput > div > div > input {{
        border-radius: 24px;
        padding: 12px 20px;
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
        background: {colors['secondary']};
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
    """渲染侧边栏"""
    with st.sidebar:
        st.markdown("## 📝 对话历史")
        
        # 新建会话按钮
        if st.button("➕ 新建对话", use_container_width=True):
            new_id = st.session_state.conversation_manager.create_new_conversation()
            st.session_state.current_conversation_id = new_id
            st.session_state.current_page = 1
            st.rerun()
        
        # 搜索框
        search_query = st.text_input("🔍 搜索对话", key="search_input")
        
        # 获取会话列表
        page_size = 10
        if search_query:
            conversations = st.session_state.conversation_manager.search_conversations(search_query)
            total_conversations = len(conversations)
            total_pages = (total_conversations + page_size - 1) // page_size if total_conversations > 0 else 1
            current_page = 1
        else:
            paginated_result = st.session_state.conversation_manager.get_conversations_list(
                page=st.session_state.current_page,
                page_size=page_size
            )
            conversations = paginated_result["conversations"]
            total_conversations = paginated_result["total"]
            total_pages = paginated_result["total_pages"]
            current_page = paginated_result["page"]
        
        # 渲染会话列表
        if conversations:
            st.markdown(f"### 会话列表 ({total_conversations}条)")
            for conv in conversations:
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
                        if not search_query:
                            new_total = len(st.session_state.conversation_manager.conversations)
                            new_total_pages = (new_total + page_size - 1) // page_size if new_total > 0 else 1
                            if current_page > new_total_pages:
                                st.session_state.current_page = max(1, new_total_pages)
                        st.rerun()
            
            # 分页控件
            if not search_query and total_pages > 1:
                st.markdown("---")
                col1, col2, col3 = st.columns([1, 2, 1])
                with col1:
                    if st.button("◀️ 上一页", use_container_width=True, disabled=current_page <= 1):
                        st.session_state.current_page = max(1, current_page - 1)
                        st.rerun()
                with col2:
                    st.markdown(f"<center>第 {current_page}/{total_pages} 页</center>", unsafe_allow_html=True)
                with col3:
                    if st.button("下一页 ▶️", use_container_width=True, disabled=current_page >= total_pages):
                        st.session_state.current_page = min(total_pages, current_page + 1)
                        st.rerun()
        else:
            st.info("暂无对话记录")
        
        st.divider()
        
        # 配置区域
        st.markdown("## ⚙️ 设置")
        
        # 运行模式
        st.markdown("### 运行模式")
        use_simulation = st.checkbox(
            "使用模拟模式",
            value=st.session_state.use_simulation,
            help="开启后使用模拟响应，无需API密钥"
        )
        st.session_state.use_simulation = use_simulation
        
        if use_simulation:
            st.info("🎯 当前运行在模拟模式")
        else:
            st.success("✅ 当前运行在真实API模式")
        
        # API配置
        st.markdown("### API配置")
        default_api_key = get_setting("DEEPSEEK_API_KEY") or get_setting("OPENAI_API_KEY") or ""
        default_base_url = get_setting("LLM_BASE_URL", DEFAULT_BASE_URL)
        default_model = get_setting("LLM_MODEL", DEFAULT_MODEL)
        
        api_key = st.text_input("🔑 API Key", value=default_api_key, type="password")
        base_url = st.text_input("🌐 Base URL", value=default_base_url)
        model = st.text_input("🤖 Model", value=default_model)
        
        # 角色预设
        st.markdown("### 角色预设")
        role_options = list(ROLE_PRESETS.keys())
        selected_role = st.selectbox("选择角色", options=role_options, index=0)
        
        # 系统提示词
        st.markdown("### 系统提示词")
        system_prompt = st.text_area(
            "设置AI角色",
            value=ROLE_PRESETS[selected_role],
            height=100
        )
        
        # 参数调节
        st.markdown("### 参数调节")
        
        context_memory_limit = st.slider(
            "📚 上下文记忆数量",
            min_value=0,
            max_value=20,
            value=st.session_state.context_memory_limit,
            step=1,
            help="保留最近N条历史消息作为上下文"
        )
        st.session_state.context_memory_limit = context_memory_limit
        
        temperature = st.slider(
            "🌡️ Temperature (创造性)",
            min_value=0.0,
            max_value=2.0,
            value=0.7,
            step=0.1,
            help="控制输出的随机性"
        )
        
        max_tokens = st.slider(
            "📏 Max Tokens (最大长度)",
            min_value=100,
            max_value=4000,
            value=2000,
            step=100,
            help="单次回复的最大token数"
        )
        
        top_p = st.slider(
            "🎯 Top P (核采样)",
            min_value=0.0,
            max_value=1.0,
            value=1.0,
            step=0.05,
            help="核采样概率"
        )
        
        # 主题切换
        st.markdown("### 界面设置")
        theme_options = ["light", "dark"]
        new_theme = st.selectbox("🎨 主题模式", theme_options, index=theme_options.index(theme))
        if new_theme != theme:
            st.session_state.theme = new_theme
            st.rerun()
        
        # 清除对话按钮
        st.divider()
        if st.button("🗑️ 清除当前对话", use_container_width=True):
            if st.session_state.conversation_manager.reset_current_conversation():
                st.success("对话已清除")
                st.rerun()
            else:
                st.error("清除失败")


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
    """处理用户输入"""
    # 防抖检查
    current_time = time.time()
    if current_time - st.session_state.debounce_timer < DEBOUNCE_INTERVAL:
        return
    
    st.session_state.debounce_timer = current_time
    
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
        
        full_response = []
        response_placeholder = st.empty()
        
        try:
            # 获取历史消息
            all_messages = st.session_state.conversation_manager.get_messages()
            
            # 构建消息列表
            if st.session_state.context_memory_limit > 0 and len(all_messages) > 1:
                # 使用上下文记忆
                history_messages = all_messages[:-1]
                
                if len(history_messages) > st.session_state.context_memory_limit:
                    history_messages = history_messages[-st.session_state.context_memory_limit:]
                
                # 获取当前选择的角色提示词
                role_options = list(ROLE_PRESETS.keys())
                selected_role = st.session_state.get("selected_role", "星期八")
                system_prompt = ROLE_PRESETS.get(selected_role, ROLE_PRESETS["星期八"])
                
                built_messages = [{"role": "system", "content": system_prompt}]
                built_messages.extend(history_messages)
                built_messages.append({"role": "user", "content": user_input})
                
                context_info = f"📝 已加载 {len(history_messages)} 条历史消息作为上下文"
                thinking_placeholder.markdown(context_info)
            else:
                # 不使用上下文记忆
                role_options = list(ROLE_PRESETS.keys())
                selected_role = st.session_state.get("selected_role", "星期八")
                system_prompt = ROLE_PRESETS.get(selected_role, ROLE_PRESETS["星期八"])
                
                built_messages = [{"role": "system", "content": system_prompt}]
                built_messages.append({"role": "user", "content": user_input})
                
                thinking_placeholder.markdown("🔄 正在处理您的请求...")
            
            # 获取模型参数
            default_base_url = get_setting("LLM_BASE_URL", DEFAULT_BASE_URL)
            default_model = get_setting("LLM_MODEL", DEFAULT_MODEL)
            
            model = st.session_state.get("model", default_model)
            base_url = st.session_state.get("base_url", default_base_url)
            
            # 获取参数滑块的值
            temperature = 0.7
            max_tokens = 2000
            top_p = 1.0
            
            # 根据API类型选择调用方式
            if st.session_state.use_simulation or not st.session_state.get("api_key"):
                # 模拟模式
                thinking_placeholder.markdown("🤔 模拟模式思考中...")
                for chunk in simulate_response(user_input):
                    full_response.append(chunk)
                    response_placeholder.markdown("".join(full_response))
            else:
                # 真实API调用
                thinking_placeholder.markdown("🌟 星期八正在思考...")
                
                client = OpenAI(
                    api_key=st.session_state.get("api_key", ""),
                    base_url=base_url
                )
                
                for chunk in call_api_stream(
                    client=client,
                    model=model,
                    messages=built_messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    top_p=top_p
                ):
                    full_response.append(chunk)
                    response_placeholder.markdown("".join(full_response))
            
            assistant_message = "".join(full_response)
            
            # 添加助手消息
            st.session_state.conversation_manager.add_message("assistant", assistant_message)
            
        except Exception as e:
            error_msg = f"❌ 出错了: {str(e)}"
            thinking_placeholder.markdown(error_msg)
            st.session_state.conversation_manager.add_message("assistant", error_msg)


def render_export_buttons():
    """渲染导出按钮"""
    col1, col2 = st.columns(2)
    
    with col1:
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
        md_content = st.session_state.conversation_manager.export_conversation(format="markdown")
        if md_content:
            st.download_button(
                "📝 导出为Markdown",
                md_content,
                file_name="conversation.md",
                mime="text/markdown",
                use_container_width=True
            )


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
    render_export_buttons()


if __name__ == "__main__":
    main()
