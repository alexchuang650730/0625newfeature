"""
SmartUI Fusion Main Application
主應用程序入口點
"""

import asyncio
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager
import json
import logging
from typing import Dict, Any, List
import os

from .protocols.ag_ui_protocol import (
    AGUIProtocolHandler, MessageType, AGUIMessage,
    VoiceCommandMessage, VisualDebugMessage, UIModificationMessage
)
from .core.decision_engine import SmartUIDecisionEngine
from .integrations.stagewise_integration import StagewiseIntegration


# 配置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SmartUIFusionApp:
    """SmartUI Fusion 主應用程序"""
    
    def __init__(self):
        self.config = self._load_config()
        
        # 初始化核心組件
        self.protocol_handler = AGUIProtocolHandler()
        self.decision_engine = SmartUIDecisionEngine(self.config.get('decision_engine', {}))
        self.stagewise_integration = StagewiseIntegration(self.config.get('stagewise', {}))
        
        # WebSocket 連接管理
        self.active_connections: List[WebSocket] = []
        self.session_connections: Dict[str, List[WebSocket]] = {}
        
        # 註冊消息處理器
        self._register_message_handlers()
        
        # 註冊 Stagewise 事件處理器
        self._register_stagewise_handlers()
    
    def _load_config(self) -> Dict[str, Any]:
        """載入配置"""
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'app_config.json')
        
        default_config = {
            "app": {
                "host": "0.0.0.0",
                "port": 8000,
                "debug": True
            },
            "decision_engine": {
                "strategy": "hybrid",
                "confidence_threshold": 0.7,
                "learning_enabled": True
            },
            "stagewise": {
                "toolbar_port": 3001,
                "debug_mode": True,
                "auto_inject": True,
                "headless": False
            },
            "livekit": {
                "enabled": False,
                "server_url": "",
                "api_key": "",
                "api_secret": ""
            }
        }
        
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    # 合併配置
                    default_config.update(user_config)
        except Exception as e:
            logger.warning(f"Failed to load config file: {e}, using default config")
        
        return default_config
    
    def _register_message_handlers(self):
        """註冊消息處理器"""
        
        self.protocol_handler.register_handler(
            MessageType.VOICE_COMMAND,
            self._handle_voice_command
        )
        
        self.protocol_handler.register_handler(
            MessageType.VISUAL_DEBUG,
            self._handle_visual_debug
        )
        
        self.protocol_handler.register_handler(
            MessageType.UI_MODIFICATION,
            self._handle_ui_modification
        )
        
        self.protocol_handler.register_handler(
            MessageType.USER_INTERACTION,
            self._handle_user_interaction
        )
    
    def _register_stagewise_handlers(self):
        """註冊 Stagewise 事件處理器"""
        
        self.stagewise_integration.register_event_handler(
            'element_selected',
            self._on_stagewise_element_selected
        )
        
        self.stagewise_integration.register_event_handler(
            'element_modified',
            self._on_stagewise_element_modified
        )
    
    async def _handle_voice_command(self, message: VoiceCommandMessage) -> AGUIMessage:
        """處理語音指令"""
        logger.info(f"Processing voice command: {message.payload.get('transcript', '')}")
        
        # 使用決策引擎處理語音指令
        ui_modification = await self.decision_engine.process_voice_command(message)
        
        if ui_modification:
            # 執行UI修改
            success = await self.stagewise_integration.execute_modification(ui_modification)
            
            if success:
                # 廣播修改結果
                await self._broadcast_message(ui_modification)
                
                return AGUIMessage(
                    message_type=MessageType.UI_RESPONSE,
                    source='smartui_fusion',
                    target=message.source,
                    session_id=message.session_id,
                    payload={
                        'status': 'success',
                        'message': 'Voice command executed successfully',
                        'modification_id': ui_modification.payload.get('modification_id')
                    }
                )
            else:
                return AGUIMessage(
                    message_type=MessageType.ERROR_REPORT,
                    source='smartui_fusion',
                    target=message.source,
                    session_id=message.session_id,
                    payload={
                        'error': 'Failed to execute UI modification',
                        'error_code': 'EXECUTION_FAILED'
                    }
                )
        else:
            return AGUIMessage(
                message_type=MessageType.VOICE_RESPONSE,
                source='smartui_fusion',
                target=message.source,
                session_id=message.session_id,
                payload={
                    'message': 'Could not understand voice command',
                    'suggestions': ['Please try rephrasing your request']
                }
            )
    
    async def _handle_visual_debug(self, message: VisualDebugMessage) -> AGUIMessage:
        """處理可視化調試消息"""
        logger.info(f"Processing visual debug: {message.payload.get('action', '')}")
        
        # 使用決策引擎處理可視化調試
        response = await self.decision_engine.process_visual_debug(message)
        
        if response:
            # 廣播響應
            await self._broadcast_message(response)
        
        return response or AGUIMessage(
            message_type=MessageType.UI_RESPONSE,
            source='smartui_fusion',
            target=message.source,
            session_id=message.session_id,
            payload={'status': 'processed'}
        )
    
    async def _handle_ui_modification(self, message: UIModificationMessage) -> AGUIMessage:
        """處理UI修改消息"""
        logger.info(f"Processing UI modification: {message.payload.get('modification_type', '')}")
        
        # 執行修改
        success = await self.stagewise_integration.execute_modification(message)
        
        if success:
            # 廣播修改結果
            await self._broadcast_message(message)
            
            return AGUIMessage(
                message_type=MessageType.UI_RESPONSE,
                source='smartui_fusion',
                target=message.source,
                session_id=message.session_id,
                payload={
                    'status': 'success',
                    'modification_id': message.payload.get('modification_id')
                }
            )
        else:
            return AGUIMessage(
                message_type=MessageType.ERROR_REPORT,
                source='smartui_fusion',
                target=message.source,
                session_id=message.session_id,
                payload={
                    'error': 'Failed to execute UI modification',
                    'error_code': 'EXECUTION_FAILED'
                }
            )
    
    async def _handle_user_interaction(self, message: AGUIMessage) -> AGUIMessage:
        """處理用戶交互消息"""
        logger.info("Processing user interaction")
        
        # 使用決策引擎分析用戶交互
        response = await self.decision_engine.process_user_interaction(message)
        
        return response or AGUIMessage(
            message_type=MessageType.UI_RESPONSE,
            source='smartui_fusion',
            target=message.source,
            session_id=message.session_id,
            payload={'status': 'analyzed'}
        )
    
    async def _on_stagewise_element_selected(self, message: VisualDebugMessage):
        """處理 Stagewise 元素選擇事件"""
        logger.info("Element selected in Stagewise")
        
        # 處理元素選擇
        response = await self._handle_visual_debug(message)
        
        # 發送響應到前端
        if response:
            await self._broadcast_message(response)
    
    async def _on_stagewise_element_modified(self, message: UIModificationMessage):
        """處理 Stagewise 元素修改事件"""
        logger.info("Element modified in Stagewise")
        
        # 處理元素修改
        response = await self._handle_ui_modification(message)
        
        # 發送響應到前端
        if response:
            await self._broadcast_message(response)
    
    async def _broadcast_message(self, message: AGUIMessage):
        """廣播消息到所有連接的客戶端"""
        if not self.active_connections:
            return
        
        message_json = message.model_dump_json()
        disconnected = []
        
        for connection in self.active_connections:
            try:
                await connection.send_text(message_json)
            except Exception as e:
                logger.warning(f"Failed to send message to client: {e}")
                disconnected.append(connection)
        
        # 移除斷開的連接
        for connection in disconnected:
            self.active_connections.remove(connection)
    
    async def initialize(self):
        """初始化應用程序"""
        logger.info("Initializing SmartUI Fusion...")
        
        # 初始化 Stagewise 整合
        stagewise_success = await self.stagewise_integration.initialize()
        if not stagewise_success:
            logger.warning("Stagewise integration failed to initialize")
        
        logger.info("SmartUI Fusion initialized successfully")
    
    async def cleanup(self):
        """清理資源"""
        logger.info("Cleaning up SmartUI Fusion...")
        
        # 清理 Stagewise 整合
        await self.stagewise_integration.cleanup()
        
        # 關閉所有 WebSocket 連接
        for connection in self.active_connections:
            try:
                await connection.close()
            except:
                pass
        
        logger.info("SmartUI Fusion cleanup completed")


# 全局應用實例
app_instance = SmartUIFusionApp()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """應用生命週期管理"""
    # 啟動
    await app_instance.initialize()
    yield
    # 關閉
    await app_instance.cleanup()


# 創建 FastAPI 應用
app = FastAPI(
    title="SmartUI Fusion",
    description="三框架智慧UI整合平台",
    version="1.0.0",
    lifespan=lifespan
)

# 添加 CORS 中間件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 靜態文件服務
static_dir = os.path.join(os.path.dirname(__file__), '..', 'static')
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
async def root():
    """根路徑"""
    return {
        "message": "SmartUI Fusion API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """健康檢查"""
    return {
        "status": "healthy",
        "stagewise_connected": app_instance.stagewise_integration.is_connected,
        "active_connections": len(app_instance.active_connections)
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket 端點"""
    await websocket.accept()
    app_instance.active_connections.append(websocket)
    
    try:
        while True:
            # 接收消息
            data = await websocket.receive_text()
            
            try:
                # 解析消息
                message_data = json.loads(data)
                message = app_instance.protocol_handler.deserialize_message(data)
                
                # 處理消息
                response = await app_instance.protocol_handler.process_message(message)
                
                # 發送響應
                if response:
                    await websocket.send_text(response.model_dump_json())
                    
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "error": "Invalid JSON format"
                }))
            except Exception as e:
                logger.error(f"Error processing WebSocket message: {e}")
                await websocket.send_text(json.dumps({
                    "error": str(e)
                }))
                
    except WebSocketDisconnect:
        app_instance.active_connections.remove(websocket)


@app.post("/api/navigate")
async def navigate_to_url(request: dict):
    """導航到指定 URL"""
    url = request.get('url')
    if not url:
        raise HTTPException(status_code=400, detail="URL is required")
    
    try:
        await app_instance.stagewise_integration.navigate_to_url(url)
        return {"status": "success", "message": f"Navigated to {url}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/screenshot")
async def take_screenshot():
    """截取頁面截圖"""
    try:
        screenshot = await app_instance.stagewise_integration.take_screenshot()
        return {"screenshot": screenshot}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/metrics")
async def get_metrics():
    """獲取性能指標"""
    try:
        metrics = await app_instance.decision_engine.get_performance_metrics()
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def main():
    """主函數"""
    config = app_instance.config.get('app', {})
    
    uvicorn.run(
        "src.main:app",
        host=config.get('host', '0.0.0.0'),
        port=config.get('port', 8000),
        reload=config.get('debug', True),
        log_level="info"
    )


if __name__ == "__main__":
    main()

