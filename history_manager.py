"""
对话历史管理模块
负责管理对话会话的创建、存储、加载、搜索和导出功能
"""
import json
import os
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional

class ConversationManager:
    """对话会话管理器"""
    
    def __init__(self, storage_file: str = "conversations.json"):
        """
        初始化会话管理器
        
        Args:
            storage_file: 存储文件路径
        """
        self.storage_file = storage_file
        self.conversations = self.load_conversations()
        self.current_conversation_id = None
        
        # 如果没有会话，创建一个新的
        if not self.conversations:
            self.create_new_conversation()
    
    def load_conversations(self) -> List[Dict[str, Any]]:
        """
        从文件加载会话数据
        
        Returns:
            会话列表
        """
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"加载会话失败: {e}")
        return []
    
    def save_conversations(self) -> bool:
        """
        保存会话数据到文件
        
        Returns:
            是否保存成功
        """
        try:
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(self.conversations, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存会话失败: {e}")
            return False
    
    def create_new_conversation(self, title: str = None) -> str:
        """
        创建新会话
        
        Args:
            title: 会话标题
            
        Returns:
            新会话ID
        """
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
        """
        获取当前会话
        
        Returns:
            当前会话字典
        """
        if not self.current_conversation_id:
            return None
        
        for conv in self.conversations:
            if conv["id"] == self.current_conversation_id:
                return conv
        return None
    
    def set_current_conversation(self, conversation_id: str) -> bool:
        """
        设置当前会话
        
        Args:
            conversation_id: 会话ID
            
        Returns:
            是否设置成功
        """
        for conv in self.conversations:
            if conv["id"] == conversation_id:
                self.current_conversation_id = conversation_id
                return True
        return False
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """
        删除会话
        
        Args:
            conversation_id: 会话ID
            
        Returns:
            是否删除成功
        """
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
        """
        添加消息到当前会话
        
        Args:
            role: 消息角色 ('user' 或 'assistant')
            content: 消息内容
            
        Returns:
            是否添加成功
        """
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
        """
        获取会话消息
        
        Args:
            conversation_id: 会话ID，默认为当前会话
            
        Returns:
            消息列表
        """
        target_id = conversation_id or self.current_conversation_id
        
        for conv in self.conversations:
            if conv["id"] == target_id:
                return conv.get("messages", [])
        
        return []
    
    def search_conversations(self, keyword: str) -> List[Dict[str, Any]]:
        """
        搜索包含关键词的会话
        
        Args:
            keyword: 搜索关键词
            
        Returns:
            匹配的会话列表
        """
        keyword = keyword.lower()
        results = []
        
        for conv in self.conversations:
            # 搜索标题
            if keyword in conv["title"].lower():
                results.append(conv)
                continue
            
            # 搜索消息内容
            for msg in conv.get("messages", []):
                if keyword in msg["content"].lower():
                    results.append(conv)
                    break
        
        return results
    
    def get_conversations_list(self, page: int = 1, page_size: int = 10) -> Dict[str, Any]:
        """
        分页获取会话列表
        
        Args:
            page: 页码
            page_size: 每页数量
            
        Returns:
            包含会话列表和分页信息的字典
        """
        total = len(self.conversations)
        total_pages = (total + page_size - 1) // page_size
        
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        
        return {
            "conversations": self.conversations[start_idx:end_idx],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages
        }
    
    def export_conversation(self, conversation_id: str = None, format: str = "txt") -> Optional[str]:
        """
        导出会话内容
        
        Args:
            conversation_id: 会话ID，默认为当前会话
            format: 导出格式 ('txt' 或 'markdown')
            
        Returns:
            导出的内容字符串
        """
        conversation = None
        
        if conversation_id:
            for conv in self.conversations:
                if conv["id"] == conversation_id:
                    conversation = conv
                    break
        else:
            conversation = self.get_current_conversation()
        
        if not conversation:
            return None
        
        if format == "markdown":
            return self._export_as_markdown(conversation)
        else:
            return self._export_as_txt(conversation)
    
    def _export_as_markdown(self, conversation: Dict[str, Any]) -> str:
        """
        导出为Markdown格式
        
        Args:
            conversation: 会话字典
            
        Returns:
            Markdown格式的字符串
        """
        md = f"# {conversation['title']}\n\n"
        md += f"**创建时间**: {conversation['created_at']}\n\n"
        md += "---\n\n"
        
        for msg in conversation.get("messages", []):
            role_display = "用户" if msg["role"] == "user" else "助手"
            md += f"### {role_display} ({msg['timestamp']})\n\n"
            md += f"{msg['content']}\n\n"
            md += "---\n\n"
        
        return md
    
    def _export_as_txt(self, conversation: Dict[str, Any]) -> str:
        """
        导出为TXT格式
        
        Args:
            conversation: 会话字典
            
        Returns:
            TXT格式的字符串
        """
        txt = f"{conversation['title']}\n"
        txt += f"创建时间: {conversation['created_at']}\n"
        txt += "=" * 50 + "\n\n"
        
        for msg in conversation.get("messages", []):
            role_display = "用户" if msg["role"] == "user" else "助手"
            txt += f"[{role_display}] {msg['timestamp']}\n"
            txt += f"{msg['content']}\n\n"
            txt += "-" * 50 + "\n\n"
        
        return txt
    
    def reset_current_conversation(self) -> bool:
        """
        重置当前会话（清空消息）
        
        Returns:
            是否重置成功
        """
        conversation = self.get_current_conversation()
        if not conversation:
            return False
        
        conversation["messages"] = []
        conversation["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.save_conversations()
        return True

# 全局会话管理器实例
conversation_manager = ConversationManager()

def get_conversation_manager() -> ConversationManager:
    """获取会话管理器实例"""
    return conversation_manager
