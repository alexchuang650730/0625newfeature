"""
AG-UI Protocol Core Implementation
智慧UI通信協議的核心實現
"""

from enum import Enum
from typing import Dict, Any, Optional, Union, List
from pydantic import BaseModel, Field
from datetime import datetime
import uuid
import json


class MessageType(Enum):
    """AG-UI協議消息類型定義"""
    
    # UI操作相關
    UI_MODIFICATION = "ui_modification"
    UI_QUERY = "ui_query"
    UI_RESPONSE = "ui_response"
    
    # 語音交互相關
    VOICE_COMMAND = "voice_command"
    VOICE_RESPONSE = "voice_response"
    VOICE_STATUS = "voice_status"
    
    # 可視化調試相關
    VISUAL_DEBUG = "visual_debug"
    ELEMENT_SELECT = "element_select"
    ELEMENT_INSPECT = "element_inspect"
    
    # 狀態同步相關
    STATE_SYNC = "state_sync"
    STATE_UPDATE = "state_update"
    STATE_QUERY = "state_query"
    
    # 用戶交互相關
    USER_INTERACTION = "user_interaction"
    USER_BEHAVIOR = "user_behavior"
    USER_PREFERENCE = "user_preference"
    
    # 系統控制相關
    SYSTEM_STATUS = "system_status"
    ERROR_REPORT = "error_report"
    HEARTBEAT = "heartbeat"


class Priority(Enum):
    """消息優先級"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class AGUIMessage(BaseModel):
    """AG-UI協議基礎消息結構"""
    
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    message_type: MessageType
    timestamp: datetime = Field(default_factory=datetime.now)
    source: str
    target: Optional[str] = None
    priority: Priority = Priority.NORMAL
    version: str = "1.0"
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    payload: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class VoiceCommandMessage(AGUIMessage):
    """語音指令消息"""
    
    message_type: MessageType = MessageType.VOICE_COMMAND
    
    def __init__(self, **data):
        super().__init__(**data)
        self.payload.update({
            "transcript": data.get("transcript", ""),
            "intent": data.get("intent", {}),
            "confidence": data.get("confidence", 0.0),
            "language": data.get("language", "zh-TW"),
            "audio_duration": data.get("audio_duration", 0.0)
        })


class VisualDebugMessage(AGUIMessage):
    """可視化調試消息"""
    
    message_type: MessageType = MessageType.VISUAL_DEBUG
    
    def __init__(self, **data):
        super().__init__(**data)
        self.payload.update({
            "element_id": data.get("element_id", ""),
            "action": data.get("action", ""),  # select, modify, inspect, highlight
            "properties": data.get("properties", {}),
            "dom_path": data.get("dom_path", ""),
            "screenshot_data": data.get("screenshot_data"),
            "coordinates": data.get("coordinates", {})
        })


class UIModificationMessage(AGUIMessage):
    """UI修改消息"""
    
    message_type: MessageType = MessageType.UI_MODIFICATION
    
    def __init__(self, **data):
        super().__init__(**data)
        self.payload.update({
            "modification_id": data.get("modification_id", str(uuid.uuid4())),
            "target_element": data.get("target_element", ""),
            "modification_type": data.get("modification_type", ""),  # style, content, attribute, structure
            "parameters": data.get("parameters", {}),
            "preview_mode": data.get("preview_mode", False),
            "rollback_data": data.get("rollback_data", {})
        })


class StateSyncMessage(AGUIMessage):
    """狀態同步消息"""
    
    message_type: MessageType = MessageType.STATE_SYNC
    
    def __init__(self, **data):
        super().__init__(**data)
        self.payload.update({
            "state_type": data.get("state_type", ""),  # ui_state, user_state, session_state
            "state_data": data.get("state_data", {}),
            "sync_scope": data.get("sync_scope", "session"),  # global, session, user
            "incremental": data.get("incremental", False)
        })


class UserInteractionMessage(AGUIMessage):
    """用戶交互消息"""
    
    message_type: MessageType = MessageType.USER_INTERACTION
    
    def __init__(self, **data):
        super().__init__(**data)
        self.payload.update({
            "interaction_type": data.get("interaction_type", ""),  # click, hover, scroll, input
            "element_info": data.get("element_info", {}),
            "interaction_data": data.get("interaction_data", {}),
            "context": data.get("context", {}),
            "device_info": data.get("device_info", {})
        })


class AGUIProtocolHandler:
    """AG-UI協議處理器"""
    
    def __init__(self):
        self.message_handlers: Dict[MessageType, callable] = {}
        self.middleware_stack: List[callable] = []
        self.message_queue: List[AGUIMessage] = []
        self.session_states: Dict[str, Dict[str, Any]] = {}
        
    def register_handler(self, message_type: MessageType, handler: callable):
        """註冊消息處理器"""
        self.message_handlers[message_type] = handler
        
    def add_middleware(self, middleware: callable):
        """添加中間件"""
        self.middleware_stack.append(middleware)
        
    async def process_message(self, message: Union[Dict[str, Any], AGUIMessage]) -> Optional[AGUIMessage]:
        """處理消息"""
        
        # 轉換為AGUIMessage對象
        if isinstance(message, dict):
            message = self._dict_to_message(message)
        
        # 應用中間件
        for middleware in self.middleware_stack:
            message = await middleware(message)
            if message is None:
                return None
        
        # 查找處理器
        handler = self.message_handlers.get(message.message_type)
        if handler:
            try:
                response = await handler(message)
                return response
            except Exception as e:
                return self._create_error_response(message, str(e))
        else:
            return self._create_error_response(message, f"No handler for message type: {message.message_type}")
    
    def _dict_to_message(self, data: Dict[str, Any]) -> AGUIMessage:
        """將字典轉換為AGUIMessage對象"""
        message_type = MessageType(data.get('message_type'))
        
        # 根據消息類型創建相應的消息對象
        message_classes = {
            MessageType.VOICE_COMMAND: VoiceCommandMessage,
            MessageType.VISUAL_DEBUG: VisualDebugMessage,
            MessageType.UI_MODIFICATION: UIModificationMessage,
            MessageType.STATE_SYNC: StateSyncMessage,
            MessageType.USER_INTERACTION: UserInteractionMessage,
        }
        
        message_class = message_classes.get(message_type, AGUIMessage)
        return message_class(**data)
    
    def _create_error_response(self, original_message: AGUIMessage, error_msg: str) -> AGUIMessage:
        """創建錯誤響應消息"""
        return AGUIMessage(
            message_type=MessageType.ERROR_REPORT,
            source="protocol_handler",
            target=original_message.source,
            session_id=original_message.session_id,
            user_id=original_message.user_id,
            payload={
                "error_message": error_msg,
                "original_message_id": original_message.message_id,
                "error_code": "HANDLER_ERROR"
            }
        )
    
    def serialize_message(self, message: AGUIMessage) -> str:
        """序列化消息為JSON字符串"""
        return message.model_dump_json()
    
    def deserialize_message(self, json_str: str) -> AGUIMessage:
        """從JSON字符串反序列化消息"""
        data = json.loads(json_str)
        return self._dict_to_message(data)


# 協議版本管理
class ProtocolVersion:
    """協議版本管理"""
    
    CURRENT_VERSION = "1.0"
    SUPPORTED_VERSIONS = ["1.0"]
    
    @classmethod
    def is_supported(cls, version: str) -> bool:
        """檢查版本是否支持"""
        return version in cls.SUPPORTED_VERSIONS
    
    @classmethod
    def get_compatibility_info(cls, version: str) -> Dict[str, Any]:
        """獲取版本兼容性信息"""
        return {
            "supported": cls.is_supported(version),
            "current_version": cls.CURRENT_VERSION,
            "migration_required": version != cls.CURRENT_VERSION
        }


# 消息路由器
class MessageRouter:
    """消息路由器"""
    
    def __init__(self):
        self.routes: Dict[str, str] = {}  # target -> endpoint
        self.load_balancers: Dict[str, callable] = {}
        
    def register_route(self, target: str, endpoint: str):
        """註冊路由"""
        self.routes[target] = endpoint
        
    def register_load_balancer(self, target: str, balancer: callable):
        """註冊負載均衡器"""
        self.load_balancers[target] = balancer
        
    def route_message(self, message: AGUIMessage) -> str:
        """路由消息到目標端點"""
        target = message.target
        if not target:
            return None
            
        # 檢查是否有負載均衡器
        if target in self.load_balancers:
            return self.load_balancers[target](message)
            
        # 使用直接路由
        return self.routes.get(target)


# 導出主要類和函數
__all__ = [
    'MessageType',
    'Priority', 
    'AGUIMessage',
    'VoiceCommandMessage',
    'VisualDebugMessage', 
    'UIModificationMessage',
    'StateSyncMessage',
    'UserInteractionMessage',
    'AGUIProtocolHandler',
    'ProtocolVersion',
    'MessageRouter'
]

