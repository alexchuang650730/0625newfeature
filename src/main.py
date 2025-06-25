"""
SmartUI Fusion Main Application
三框架智慧UI整合平台的主應用程序 - 深度整合 smartui_mcp

整合框架：
- Stagewise: 前端可視化調試工具
- LiveKit: 語音AI交互框架  
- AG-UI Protocol: 統一通信協議
- smartui_mcp: 智能決策引擎 (深度整合)

作者: SmartUI Fusion Team
版本: 1.0.0
"""

import asyncio
import logging
import json
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from .protocols.ag_ui_protocol import (
    AGUIProtocolHandler, VoiceCommandMessage, VisualDebugMessage,
    UIModificationMessage, StateSyncMessage, UserInteractionMessage
)
from .core.enhanced_decision_engine import EnhancedDecisionEngine, DecisionContext, UserInteraction, InteractionType
from .core.smartui_user_analyzer import SmartUIUserAnalyzer
from .integrations.stagewise_integration import StagewiseIntegration


class SmartUIFusionApp:
    """SmartUI Fusion 主應用程序 - 深度整合 smartui_mcp"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.app = FastAPI(
            title="SmartUI Fusion - Enhanced with SmartUI MCP",
            description="三框架智慧UI整合平台 - 深度整合 smartui_mcp 智能分析",
            version="1.0.0"
        )
        
        # 載入配置
        self.config = self._load_config(config_path)
        
        # 初始化日誌
        self.logger = self._setup_logging()
        
        # 初始化核心組件
        self.protocol_handler = AGUIProtocolHandler()
        
        # 使用增強的決策引擎（整合 smartui_mcp）
        self.decision_engine = EnhancedDecisionEngine(self.config.get('decision_engine', {}))
        
        # SmartUI 用戶分析器
        self.user_analyzer = SmartUIUserAnalyzer(self.config.get('user_analyzer', {}))
        
        # Stagewise 整合
        self.stagewise = StagewiseIntegration(self.config.get('stagewise', {}))
        
        # WebSocket 連接管理
        self.active_connections: Dict[str, WebSocket] = {}
        
        # 用戶會話管理
        self.user_sessions: Dict[str, Dict[str, Any]] = {}
        
        # 設置路由和中間件
        self._setup_middleware()
        self._setup_routes()
        
        self.logger.info("SmartUI Fusion App initialized with SmartUI MCP integration")
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """載入配置文件"""
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "app_config.json"
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Failed to load config: {e}")
            return {}
    
    def _setup_logging(self) -> logging.Logger:
        """設置日誌系統"""
        log_config = self.config.get('logging', {})
        
        logging.basicConfig(
            level=getattr(logging, log_config.get('level', 'INFO')),
            format=log_config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        )
        
        return logging.getLogger(__name__)
    
    def _setup_middleware(self):
        """設置中間件"""
        # CORS 中間件
        cors_origins = self.config.get('security', {}).get('cors_origins', ["*"])
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    def _setup_routes(self):
        """設置路由"""
        
        @self.app.get("/")
        async def root():
            return {
                "message": "SmartUI Fusion API - Enhanced with SmartUI MCP", 
                "version": "1.0.0", 
                "status": "running",
                "features": [
                    "Voice Command Processing",
                    "Visual Debug Integration", 
                    "Smart User Analysis",
                    "Adaptive UI Generation",
                    "Multi-framework Decision Engine"
                ]
            }
        
        @self.app.get("/health")
        async def health_check():
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "components": {
                    "enhanced_decision_engine": "active",
                    "smartui_user_analyzer": "active",
                    "stagewise_integration": "active",
                    "protocol_handler": "active"
                }
            }
        
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            await self._handle_websocket_connection(websocket)
        
        @self.app.post("/api/navigate")
        async def navigate_to_url(request: dict):
            """導航到指定URL"""
            url = request.get('url')
            user_id = request.get('user_id', 'anonymous')
            
            if not url:
                raise HTTPException(status_code=400, detail="URL is required")
            
            try:
                # 記錄用戶交互
                await self._record_user_interaction(
                    user_id=user_id,
                    interaction_type=InteractionType.MOUSE,
                    action="navigate",
                    element_id="navigation",
                    context={"url": url},
                    success=True
                )
                
                result = await self.stagewise.navigate_to_url(url)
                return {"success": True, "result": result}
            except Exception as e:
                # 記錄失敗的交互
                await self._record_user_interaction(
                    user_id=user_id,
                    interaction_type=InteractionType.MOUSE,
                    action="navigate",
                    element_id="navigation",
                    context={"url": url, "error": str(e)},
                    success=False,
                    error_message=str(e)
                )
                
                self.logger.error(f"Navigation failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/screenshot")
        async def take_screenshot():
            """截取當前頁面截圖"""
            try:
                screenshot_path = await self.stagewise.take_screenshot()
                return {"success": True, "screenshot_path": screenshot_path}
            except Exception as e:
                self.logger.error(f"Screenshot failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/metrics")
        async def get_metrics():
            """獲取系統性能指標"""
            try:
                decision_metrics = await self.decision_engine.get_performance_metrics()
                return {"success": True, "metrics": decision_metrics}
            except Exception as e:
                self.logger.error(f"Failed to get metrics: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/user/{user_id}/profile")
        async def get_user_profile(user_id: str):
            """獲取用戶檔案和分析"""
            try:
                user_insights = await self.user_analyzer.get_user_insights(user_id)
                return {"success": True, "user_insights": user_insights}
            except Exception as e:
                self.logger.error(f"Failed to get user profile: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/user/{user_id}/interaction")
        async def record_user_interaction(user_id: str, interaction_data: dict):
            """記錄用戶交互"""
            try:
                interaction = UserInteraction(
                    interaction_id=interaction_data.get('interaction_id', f"int_{datetime.now().timestamp()}"),
                    user_id=user_id,
                    session_id=interaction_data.get('session_id', 'default'),
                    timestamp=datetime.now(),
                    interaction_type=InteractionType(interaction_data.get('interaction_type', 'mouse')),
                    element_id=interaction_data.get('element_id'),
                    element_type=interaction_data.get('element_type'),
                    action=interaction_data.get('action', 'unknown'),
                    context=interaction_data.get('context', {}),
                    success=interaction_data.get('success', True),
                    duration=interaction_data.get('duration', 0),
                    error_message=interaction_data.get('error_message')
                )
                
                success = await self.user_analyzer.record_interaction(interaction)
                
                if success:
                    return {"success": True, "message": "Interaction recorded"}
                else:
                    raise HTTPException(status_code=500, detail="Failed to record interaction")
                    
            except Exception as e:
                self.logger.error(f"Failed to record interaction: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/user/{user_id}/analyze")
        async def analyze_user_behavior(user_id: str, context: dict = None):
            """分析用戶行為"""
            try:
                analysis = await self.user_analyzer.analyze_user_behavior(user_id, context)
                return {"success": True, "analysis": analysis}
            except Exception as e:
                self.logger.error(f"Failed to analyze user behavior: {e}")
                raise HTTPException(status_code=500, detail=str(e))
    
    async def _handle_websocket_connection(self, websocket: WebSocket):
        """處理 WebSocket 連接"""
        await websocket.accept()
        connection_id = f"conn_{len(self.active_connections)}"
        self.active_connections[connection_id] = websocket
        
        self.logger.info(f"WebSocket connection established: {connection_id}")
        
        try:
            while True:
                # 接收消息
                data = await websocket.receive_text()
                message_data = json.loads(data)
                
                # 處理消息
                response = await self._process_websocket_message(message_data, connection_id)
                
                # 發送響應
                await websocket.send_text(json.dumps(response))
                
        except WebSocketDisconnect:
            self.logger.info(f"WebSocket connection closed: {connection_id}")
        except Exception as e:
            self.logger.error(f"WebSocket error: {e}")
        finally:
            if connection_id in self.active_connections:
                del self.active_connections[connection_id]
    
    async def _process_websocket_message(self, message_data: Dict[str, Any], connection_id: str) -> Dict[str, Any]:
        """處理 WebSocket 消息"""
        try:
            message_type = message_data.get('message_type')
            user_id = message_data.get('user_id', 'anonymous')
            
            # 記錄 WebSocket 交互
            await self._record_user_interaction(
                user_id=user_id,
                interaction_type=InteractionType.KEYBOARD,  # WebSocket 通常是鍵盤觸發
                action=f"websocket_{message_type}",
                element_id="websocket_interface",
                context={"connection_id": connection_id, "message_type": message_type},
                success=True
            )
            
            if message_type == 'voice_command':
                return await self._handle_voice_command(message_data)
            elif message_type == 'visual_debug':
                return await self._handle_visual_debug(message_data)
            elif message_type == 'user_interaction':
                return await self._handle_user_interaction(message_data)
            else:
                return {
                    "success": False,
                    "error": f"Unknown message type: {message_type}"
                }
                
        except Exception as e:
            self.logger.error(f"Message processing error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _handle_voice_command(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """處理語音指令"""
        try:
            voice_message = VoiceCommandMessage(**message_data)
            
            # 記錄語音交互
            await self._record_user_interaction(
                user_id=voice_message.user_id,
                interaction_type=InteractionType.VOICE,
                action="voice_command",
                element_id="voice_interface",
                context={
                    "transcript": voice_message.payload.get('transcript', ''),
                    "confidence": voice_message.payload.get('confidence', 0)
                },
                success=True,
                duration=voice_message.payload.get('duration', 0)
            )
            
            # 使用增強的決策引擎處理
            ui_modification = await self.decision_engine.process_voice_command(voice_message)
            
            if ui_modification:
                return {
                    "success": True,
                    "message_type": "ui_modification",
                    "data": ui_modification.to_dict()
                }
            else:
                return {
                    "success": False,
                    "error": "Unable to process voice command"
                }
                
        except Exception as e:
            # 記錄失敗的語音交互
            user_id = message_data.get('user_id', 'anonymous')
            await self._record_user_interaction(
                user_id=user_id,
                interaction_type=InteractionType.VOICE,
                action="voice_command",
                element_id="voice_interface",
                context={"error": str(e)},
                success=False,
                error_message=str(e)
            )
            
            return {"success": False, "error": str(e)}
    
    async def _handle_visual_debug(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """處理可視化調試"""
        try:
            visual_message = VisualDebugMessage(**message_data)
            
            # 記錄視覺調試交互
            await self._record_user_interaction(
                user_id=visual_message.user_id,
                interaction_type=InteractionType.VISUAL,
                action="visual_debug",
                element_id=visual_message.payload.get('selected_element', {}).get('id', 'unknown'),
                context={
                    "debug_action": visual_message.payload.get('debug_action', ''),
                    "selected_element": visual_message.payload.get('selected_element', {})
                },
                success=True
            )
            
            # 使用增強的決策引擎處理
            ui_modification = await self.decision_engine.process_visual_debug(visual_message)
            
            if ui_modification:
                return {
                    "success": True,
                    "message_type": "ui_modification", 
                    "data": ui_modification.to_dict()
                }
            else:
                return {
                    "success": False,
                    "error": "Unable to process visual debug command"
                }
                
        except Exception as e:
            # 記錄失敗的視覺調試交互
            user_id = message_data.get('user_id', 'anonymous')
            await self._record_user_interaction(
                user_id=user_id,
                interaction_type=InteractionType.VISUAL,
                action="visual_debug",
                element_id="visual_interface",
                context={"error": str(e)},
                success=False,
                error_message=str(e)
            )
            
            return {"success": False, "error": str(e)}
    
    async def _handle_user_interaction(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """處理用戶交互"""
        try:
            interaction_message = UserInteractionMessage(**message_data)
            
            # 創建 UserInteraction 對象並記錄
            user_interaction = UserInteraction(
                interaction_id=f"ui_{datetime.now().timestamp()}",
                user_id=interaction_message.user_id,
                session_id=interaction_message.session_id,
                timestamp=datetime.now(),
                interaction_type=InteractionType(interaction_message.payload.get('interaction_type', 'mouse')),
                element_id=interaction_message.payload.get('element_id'),
                element_type=interaction_message.payload.get('element_type'),
                action=interaction_message.payload.get('action', 'unknown'),
                context=interaction_message.payload.get('context', {}),
                success=interaction_message.payload.get('success', True),
                duration=interaction_message.payload.get('duration', 0)
            )
            
            success = await self.user_analyzer.record_interaction(user_interaction)
            
            if success:
                # 觸發實時分析
                analysis = await self.user_analyzer.analyze_user_behavior(
                    interaction_message.user_id, 
                    interaction_message.payload.get('context', {})
                )
                
                return {
                    "success": True,
                    "message_type": "interaction_recorded",
                    "data": {
                        "recorded": True,
                        "real_time_analysis": analysis
                    }
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to record interaction"
                }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _record_user_interaction(self, user_id: str, interaction_type: InteractionType,
                                     action: str, element_id: str, context: Dict[str, Any],
                                     success: bool, duration: float = 0, 
                                     error_message: Optional[str] = None):
        """記錄用戶交互的輔助方法"""
        try:
            interaction = UserInteraction(
                interaction_id=f"auto_{datetime.now().timestamp()}",
                user_id=user_id,
                session_id=self._get_or_create_session_id(user_id),
                timestamp=datetime.now(),
                interaction_type=interaction_type,
                element_id=element_id,
                element_type=context.get('element_type'),
                action=action,
                context=context,
                success=success,
                duration=duration,
                error_message=error_message
            )
            
            await self.user_analyzer.record_interaction(interaction)
            
        except Exception as e:
            self.logger.error(f"Failed to record user interaction: {e}")
    
    def _get_or_create_session_id(self, user_id: str) -> str:
        """獲取或創建用戶會話ID"""
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = {
                'session_id': f"session_{user_id}_{datetime.now().timestamp()}",
                'start_time': datetime.now(),
                'last_activity': datetime.now()
            }
        else:
            self.user_sessions[user_id]['last_activity'] = datetime.now()
        
        return self.user_sessions[user_id]['session_id']
    
    async def start_server(self):
        """啟動服務器"""
        try:
            # 初始化組件
            await self.stagewise.initialize()
            
            self.logger.info("SmartUI Fusion server starting with SmartUI MCP integration...")
            
            # 啟動 FastAPI 服務器
            config = uvicorn.Config(
                self.app,
                host=self.config.get('app', {}).get('host', '0.0.0.0'),
                port=self.config.get('app', {}).get('port', 8000),
                log_level=self.config.get('logging', {}).get('level', 'info').lower()
            )
            
            server = uvicorn.Server(config)
            await server.serve()
            
        except Exception as e:
            self.logger.error(f"Failed to start server: {e}")
            raise


async def main():
    """主函數"""
    app = SmartUIFusionApp()
    await app.start_server()


if __name__ == "__main__":
    asyncio.run(main())

