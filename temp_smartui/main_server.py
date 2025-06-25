"""
SmartUI MCP 主服务器

这是SmartUI MCP的主要入口点，负责初始化和协调所有组件。
它将enhancedsmartui的智能感知能力与smartui_fixed的UI基础完美融合。

基于三层架构：
- coding_plugin_orchestrator (产品级)
- workflow orchestrator (工作流级)  
- mcp/adapter组件 (组件级) ← SmartUI MCP在这里

作者: Manus AI
版本: 1.0.0
"""

import asyncio
import logging
import signal
import sys
from pathlib import Path
from typing import Optional

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config.config_manager import ConfigManager
from src.common.event_bus import EventBus, EventBusEventType as EventType
from src.core_intelligence.user_analyzer import UserAnalyzer
from src.core_intelligence.decision_engine import DecisionEngine
from src.core_intelligence.api_state_manager import ApiStateManager
from src.core_intelligence.ui_generator import UIGenerator
from src.core_intelligence.mcp_integration import MCPIntegration
from src.ui_renderer.fixed_ui_renderer import FixedUIRenderer
from src.ui_renderer.smart_ui_adapter import SmartUIAdapter
from src.mcp_communication.mcp_protocol import MCPProtocol
from src.mcp_communication.event_listener import EventListener
from src.mcp_communication.release_management_integration import ReleaseManagementIntegration
from src.mcp_communication.coordinator_integration import (
    CoordinatorIntegration,
    ComponentCapability,
    OrchestrationLevel
)


class SmartUIMCPServer:
    """
    SmartUI MCP 主服务器
    
    负责初始化和协调所有智能感知组件，提供统一的MCP服务接口。
    作为组件级adapter，能够被上层的workflow orchestrator和coding_plugin_orchestrator调用。
    """
    
    def __init__(self, config_path: Optional[str] = None):
        # 初始化日志
        self.logger = self._setup_logging()
        
        # 初始化配置管理器
        self.config_manager = ConfigManager(config_path)
        
        # 初始化事件总线
        self.event_bus = EventBus()
        
        # 组件实例
        self.user_analyzer: Optional[UserAnalyzer] = None
        self.decision_engine: Optional[DecisionEngine] = None
        self.api_state_manager: Optional[ApiStateManager] = None
        self.ui_generator: Optional[UIGenerator] = None
        self.mcp_integration: Optional[MCPIntegration] = None
        self.fixed_ui_renderer: Optional[FixedUIRenderer] = None
        self.smart_ui_adapter: Optional[SmartUIAdapter] = None
        self.mcp_protocol: Optional[MCPProtocol] = None
        self.event_listener: Optional[EventListener] = None
        self.release_management: Optional[ReleaseManagementIntegration] = None
        self.coordinator_integration: Optional[CoordinatorIntegration] = None
        
        # 服务器状态
        self.is_running = False
        self.shutdown_event = asyncio.Event()
        
        self.logger.info("SmartUI MCP Server initialized")
    
    def _setup_logging(self) -> logging.Logger:
        """设置日志系统"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler('smartui_mcp.log')
            ]
        )
        return logging.getLogger(__name__)
    
    async def initialize_components(self):
        """初始化所有组件"""
        try:
            self.logger.info("Initializing SmartUI MCP components...")
            
            # 1. 初始化核心智能组件
            await self._initialize_core_intelligence()
            
            # 2. 初始化UI渲染组件
            await self._initialize_ui_renderer()
            
            # 3. 初始化MCP通信组件
            await self._initialize_mcp_communication()
            
            # 4. 初始化协调器集成
            await self._initialize_coordinator_integration()
            
            # 5. 建立组件间连接
            await self._connect_components()
            
            self.logger.info("All components initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize components: {e}")
            raise
    
    async def _initialize_core_intelligence(self):
        """初始化核心智能组件"""
        # 用户分析器
        self.user_analyzer = UserAnalyzer(
            event_bus=self.event_bus,
            config_manager=self.config_manager,
            logger=self.logger.getChild("user_analyzer")
        )
        
        # API状态管理器
        self.api_state_manager = ApiStateManager(
            event_bus=self.event_bus,
            config_manager=self.config_manager,
            logger=self.logger.getChild("api_state_manager")
        )
        
        # 决策引擎
        self.decision_engine = DecisionEngine(
            event_bus=self.event_bus,
            config_manager=self.config_manager,
            user_analyzer=self.user_analyzer,
            api_state_manager=self.api_state_manager,
            logger=self.logger.getChild("decision_engine")
        )
        
        # UI生成器
        self.ui_generator = UIGenerator(
            event_bus=self.event_bus,
            config_manager=self.config_manager,
            decision_engine=self.decision_engine,
            logger=self.logger.getChild("ui_generator")
        )
        
        # MCP集成
        self.mcp_integration = MCPIntegration(
            event_bus=self.event_bus,
            config_manager=self.config_manager,
            logger=self.logger.getChild("mcp_integration")
        )
    
    async def _initialize_ui_renderer(self):
        """初始化UI渲染组件"""
        # 固定UI渲染器
        self.fixed_ui_renderer = FixedUIRenderer(
            event_bus=self.event_bus,
            config_manager=self.config_manager,
            logger=self.logger.getChild("fixed_ui_renderer")
        )
        
        # 智能UI适配器
        self.smart_ui_adapter = SmartUIAdapter(
            event_bus=self.event_bus,
            config_manager=self.config_manager,
            ui_generator=self.ui_generator,
            fixed_ui_renderer=self.fixed_ui_renderer,
            logger=self.logger.getChild("smart_ui_adapter")
        )
    
    async def _initialize_mcp_communication(self):
        """初始化MCP通信组件"""
        # MCP协议处理器
        self.mcp_protocol = MCPProtocol(
            event_bus=self.event_bus,
            config_manager=self.config_manager,
            logger=self.logger.getChild("mcp_protocol")
        )
        
        # 事件监听器
        self.event_listener = EventListener(
            event_bus=self.event_bus,
            mcp_protocol=self.mcp_protocol,
            logger=self.logger.getChild("event_listener")
        )
        
        # 发布管理集成
        self.release_management = ReleaseManagementIntegration(
            component_id="smartui_mcp",
            event_bus=self.event_bus,
            config_manager=self.config_manager,
            logger=self.logger.getChild("release_management")
        )
    
    async def _initialize_coordinator_integration(self):
        """初始化协调器集成"""
        self.coordinator_integration = CoordinatorIntegration(
            component_id="smartui_mcp",
            event_bus=self.event_bus,
            config_manager=self.config_manager,
            logger=self.logger.getChild("coordinator_integration")
        )
        
        # 注册能力处理器
        await self._register_capability_handlers()
    
    async def _register_capability_handlers(self):
        """注册组件能力处理器"""
        # UI生成能力
        self.coordinator_integration.register_capability_handler(
            ComponentCapability.UI_GENERATION,
            self._handle_ui_generation
        )
        
        # 用户分析能力
        self.coordinator_integration.register_capability_handler(
            ComponentCapability.USER_ANALYSIS,
            self._handle_user_analysis
        )
        
        # 智能适配能力
        self.coordinator_integration.register_capability_handler(
            ComponentCapability.INTELLIGENT_ADAPTATION,
            self._handle_intelligent_adaptation
        )
        
        # 主题管理能力
        self.coordinator_integration.register_capability_handler(
            ComponentCapability.THEME_MANAGEMENT,
            self._handle_theme_management
        )
        
        # 布局优化能力
        self.coordinator_integration.register_capability_handler(
            ComponentCapability.LAYOUT_OPTIMIZATION,
            self._handle_layout_optimization
        )
        
        # 组件渲染能力
        self.coordinator_integration.register_capability_handler(
            ComponentCapability.COMPONENT_RENDERING,
            self._handle_component_rendering
        )
        
        # 事件处理能力
        self.coordinator_integration.register_capability_handler(
            ComponentCapability.EVENT_HANDLING,
            self._handle_event_handling
        )
        
        # 状态管理能力
        self.coordinator_integration.register_capability_handler(
            ComponentCapability.STATE_MANAGEMENT,
            self._handle_state_management
        )
        
        # 可访问性支持能力
        self.coordinator_integration.register_capability_handler(
            ComponentCapability.ACCESSIBILITY_SUPPORT,
            self._handle_accessibility_support
        )
        
        # 性能优化能力
        self.coordinator_integration.register_capability_handler(
            ComponentCapability.PERFORMANCE_OPTIMIZATION,
            self._handle_performance_optimization
        )
    
    async def _handle_ui_generation(self, parameters: dict) -> dict:
        """处理UI生成请求"""
        try:
            if self.ui_generator:
                result = await self.ui_generator.generate_ui_config(parameters)
                return {"success": True, "ui_config": result}
            else:
                return {"success": False, "error": "UI Generator not initialized"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _handle_user_analysis(self, parameters: dict) -> dict:
        """处理用户分析请求"""
        try:
            if self.user_analyzer:
                result = await self.user_analyzer.analyze_user_behavior(parameters)
                return {"success": True, "analysis": result}
            else:
                return {"success": False, "error": "User Analyzer not initialized"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _handle_intelligent_adaptation(self, parameters: dict) -> dict:
        """处理智能适配请求"""
        try:
            if self.decision_engine:
                result = await self.decision_engine.make_adaptation_decision(parameters)
                return {"success": True, "adaptation": result}
            else:
                return {"success": False, "error": "Decision Engine not initialized"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _handle_theme_management(self, parameters: dict) -> dict:
        """处理主题管理请求"""
        try:
            if self.smart_ui_adapter:
                result = await self.smart_ui_adapter.apply_theme(parameters)
                return {"success": True, "theme": result}
            else:
                return {"success": False, "error": "Smart UI Adapter not initialized"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _handle_layout_optimization(self, parameters: dict) -> dict:
        """处理布局优化请求"""
        try:
            if self.ui_generator:
                result = await self.ui_generator.optimize_layout(parameters)
                return {"success": True, "layout": result}
            else:
                return {"success": False, "error": "UI Generator not initialized"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _handle_component_rendering(self, parameters: dict) -> dict:
        """处理组件渲染请求"""
        try:
            if self.fixed_ui_renderer:
                result = await self.fixed_ui_renderer.render_component(parameters)
                return {"success": True, "rendered": result}
            else:
                return {"success": False, "error": "Fixed UI Renderer not initialized"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _handle_event_handling(self, parameters: dict) -> dict:
        """处理事件处理请求"""
        try:
            if self.event_listener:
                result = await self.event_listener.handle_ui_event(parameters)
                return {"success": True, "event_result": result}
            else:
                return {"success": False, "error": "Event Listener not initialized"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _handle_state_management(self, parameters: dict) -> dict:
        """处理状态管理请求"""
        try:
            if self.api_state_manager:
                result = await self.api_state_manager.manage_state(parameters)
                return {"success": True, "state": result}
            else:
                return {"success": False, "error": "API State Manager not initialized"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _handle_accessibility_support(self, parameters: dict) -> dict:
        """处理可访问性支持请求"""
        try:
            if self.smart_ui_adapter:
                result = await self.smart_ui_adapter.apply_accessibility_features(parameters)
                return {"success": True, "accessibility": result}
            else:
                return {"success": False, "error": "Smart UI Adapter not initialized"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _handle_performance_optimization(self, parameters: dict) -> dict:
        """处理性能优化请求"""
        try:
            if self.ui_generator:
                result = await self.ui_generator.optimize_performance(parameters)
                return {"success": True, "optimization": result}
            else:
                return {"success": False, "error": "UI Generator not initialized"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _connect_components(self):
        """建立组件间连接"""
        # 启动所有组件
        components = [
            self.user_analyzer,
            self.api_state_manager,
            self.decision_engine,
            self.ui_generator,
            self.mcp_integration,
            self.fixed_ui_renderer,
            self.smart_ui_adapter,
            self.mcp_protocol,
            self.event_listener,
            self.release_management,
            self.coordinator_integration
        ]
        
        for component in components:
            if hasattr(component, 'start'):
                await component.start()
        
        # 发布系统启动事件
        await self.event_bus.publish(
            EventType.SYSTEM_STARTED,
            {
                "server": "smartui_mcp",
                "components": len(components),
                "timestamp": asyncio.get_event_loop().time()
            }
        )
    
    async def start_server(self):
        """启动服务器"""
        try:
            self.logger.info("Starting SmartUI MCP Server...")
            
            # 初始化组件
            await self.initialize_components()
            
            # 注册到发布管理MCP
            await self._register_to_release_management()
            
            # 注册到协调器
            await self._register_to_coordinators()
            
            # 设置信号处理
            self._setup_signal_handlers()
            
            self.is_running = True
            self.logger.info("SmartUI MCP Server started successfully")
            
            # 等待关闭信号
            await self.shutdown_event.wait()
            
        except Exception as e:
            self.logger.error(f"Failed to start server: {e}")
            raise
    
    async def _register_to_release_management(self):
        """注册到发布管理MCP"""
        try:
            capabilities = [
                "ui_generation",
                "user_behavior_analysis", 
                "intelligent_adaptation",
                "theme_management",
                "layout_optimization",
                "component_rendering",
                "event_handling",
                "state_management"
            ]
            
            success = await self.release_management.register_module(
                module_name="SmartUI MCP",
                module_version="1.0.0",
                capabilities=capabilities,
                endpoints={
                    "health": "/health",
                    "ui_config": "/api/ui/config",
                    "user_analysis": "/api/analysis/user",
                    "state_management": "/api/state"
                },
                health_check_url="/health"
            )
            
            if success:
                self.logger.info("Successfully registered to Release Management MCP")
            else:
                self.logger.warning("Failed to register to Release Management MCP")
                
        except Exception as e:
            self.logger.error(f"Error registering to Release Management MCP: {e}")
    
    async def _register_to_coordinators(self):
        """注册到协调器"""
        try:
            capabilities = [
                ComponentCapability.UI_GENERATION,
                ComponentCapability.USER_ANALYSIS,
                ComponentCapability.INTELLIGENT_ADAPTATION,
                ComponentCapability.THEME_MANAGEMENT,
                ComponentCapability.LAYOUT_OPTIMIZATION,
                ComponentCapability.COMPONENT_RENDERING,
                ComponentCapability.EVENT_HANDLING,
                ComponentCapability.STATE_MANAGEMENT,
                ComponentCapability.ACCESSIBILITY_SUPPORT,
                ComponentCapability.PERFORMANCE_OPTIMIZATION
            ]
            
            success = await self.coordinator_integration.register_component(
                component_name="SmartUI MCP",
                component_version="1.0.0",
                capabilities=capabilities,
                endpoints={
                    "health": "/health",
                    "ui_generation": "/api/ui/generate",
                    "user_analysis": "/api/analysis/user",
                    "theme_management": "/api/ui/theme",
                    "state_management": "/api/state",
                    "orchestration": "/api/orchestration"
                },
                health_check_url="/health",
                metadata={
                    "description": "智慧感知UI组件，提供智能UI生成和用户行为分析",
                    "architecture_level": "component",
                    "supported_orchestrators": ["workflow", "product"],
                    "features": [
                        "智能UI生成",
                        "用户行为分析",
                        "自适应界面",
                        "主题管理",
                        "性能优化"
                    ]
                }
            )
            
            if success:
                self.logger.info("Successfully registered to Coordinators")
            else:
                self.logger.warning("Failed to register to Coordinators")
                
        except Exception as e:
            self.logger.error(f"Error registering to Coordinators: {e}")
    
    def _setup_signal_handlers(self):
        """设置信号处理器"""
        def signal_handler(signum, frame):
            self.logger.info(f"Received signal {signum}, initiating shutdown...")
            asyncio.create_task(self.shutdown())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def shutdown(self):
        """关闭服务器"""
        try:
            self.logger.info("Shutting down SmartUI MCP Server...")
            
            self.is_running = False
            
            # 注销组件
            if self.coordinator_integration:
                await self.coordinator_integration.unregister_component()
            
            # 停止所有组件
            components = [
                self.coordinator_integration,
                self.event_listener,
                self.mcp_protocol,
                self.smart_ui_adapter,
                self.fixed_ui_renderer,
                self.mcp_integration,
                self.ui_generator,
                self.decision_engine,
                self.api_state_manager,
                self.user_analyzer,
                self.release_management
            ]
            
            for component in components:
                if component and hasattr(component, 'stop'):
                    try:
                        await component.stop()
                    except Exception as e:
                        self.logger.error(f"Error stopping component {component.__class__.__name__}: {e}")
            
            # 发布系统关闭事件
            await self.event_bus.publish(
                EventType.SYSTEM_SHUTDOWN,
                {
                    "server": "smartui_mcp",
                    "timestamp": asyncio.get_event_loop().time()
                }
            )
            
            # 触发关闭事件
            self.shutdown_event.set()
            
            self.logger.info("SmartUI MCP Server shutdown completed")
            
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")
    
    async def get_health_status(self) -> dict:
        """获取健康状态"""
        try:
            component_status = {}
            
            # 检查各组件状态
            components = {
                "user_analyzer": self.user_analyzer,
                "decision_engine": self.decision_engine,
                "api_state_manager": self.api_state_manager,
                "ui_generator": self.ui_generator,
                "mcp_integration": self.mcp_integration,
                "fixed_ui_renderer": self.fixed_ui_renderer,
                "smart_ui_adapter": self.smart_ui_adapter,
                "mcp_protocol": self.mcp_protocol,
                "event_listener": self.event_listener,
                "release_management": self.release_management,
                "coordinator_integration": self.coordinator_integration
            }
            
            for name, component in components.items():
                if component and hasattr(component, 'get_health_status'):
                    try:
                        status = await component.get_health_status()
                        component_status[name] = status
                    except Exception as e:
                        component_status[name] = {"status": "error", "error": str(e)}
                else:
                    component_status[name] = {"status": "not_initialized"}
            
            # 获取协调器连接状态
            orchestrator_connections = {}
            if self.coordinator_integration:
                orchestrator_connections = self.coordinator_integration.get_orchestrator_connections()
            
            return {
                "server_status": "running" if self.is_running else "stopped",
                "components": component_status,
                "orchestrator_connections": {
                    level.value: info for level, info in orchestrator_connections.items()
                },
                "event_bus_stats": self.event_bus.get_stats() if hasattr(self.event_bus, 'get_stats') else {},
                "timestamp": asyncio.get_event_loop().time()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting health status: {e}")
            return {
                "server_status": "error",
                "error": str(e),
                "timestamp": asyncio.get_event_loop().time()
            }


async def main():
    """主函数"""
    server = None
    try:
        # 创建服务器实例
        config_path = sys.argv[1] if len(sys.argv) > 1 else None
        server = SmartUIMCPServer(config_path)
        
        # 启动服务器
        await server.start_server()
        
    except KeyboardInterrupt:
        print("\nReceived keyboard interrupt, shutting down...")
    except Exception as e:
        print(f"Server error: {e}")
        sys.exit(1)
    finally:
        if server:
            await server.shutdown()


if __name__ == "__main__":
    asyncio.run(main())

