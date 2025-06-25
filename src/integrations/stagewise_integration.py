"""
Stagewise Integration Module
Stagewise 可視化調試工具整合模塊
"""

import asyncio
import json
import base64
from typing import Dict, Any, List, Optional, Callable
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException
import websocket
import threading
import time

from ..protocols.ag_ui_protocol import (
    AGUIMessage, MessageType, VisualDebugMessage, UIModificationMessage
)


class StagewiseIntegration:
    """Stagewise 整合核心類"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.toolbar_port = config.get('toolbar_port', 3001)
        self.debug_mode = config.get('debug_mode', True)
        self.auto_inject = config.get('auto_inject', True)
        self.websocket_url = config.get('websocket_url', f'ws://localhost:{self.toolbar_port}/ws')
        
        # WebDriver 配置
        self.driver: Optional[webdriver.Chrome] = None
        self.driver_options = self._setup_driver_options()
        
        # WebSocket 連接
        self.ws_connection: Optional[websocket.WebSocket] = None
        self.ws_thread: Optional[threading.Thread] = None
        
        # 事件處理器
        self.event_handlers: Dict[str, Callable] = {}
        
        # 狀態管理
        self.is_connected = False
        self.selected_elements: List[Dict[str, Any]] = []
        self.ui_state: Dict[str, Any] = {}
        
    def _setup_driver_options(self) -> Options:
        """設置 WebDriver 選項"""
        options = Options()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--remote-debugging-port=9222')
        
        if self.config.get('headless', False):
            options.add_argument('--headless')
            
        return options
    
    async def initialize(self) -> bool:
        """初始化 Stagewise 整合"""
        try:
            # 啟動 WebDriver
            await self._start_webdriver()
            
            # 建立 WebSocket 連接
            await self._connect_websocket()
            
            # 注入工具欄腳本
            if self.auto_inject:
                await self._inject_toolbar()
            
            self.is_connected = True
            return True
            
        except Exception as e:
            print(f"Stagewise initialization failed: {e}")
            return False
    
    async def _start_webdriver(self):
        """啟動 WebDriver"""
        self.driver = webdriver.Chrome(options=self.driver_options)
        self.driver.implicitly_wait(10)
    
    async def _connect_websocket(self):
        """建立 WebSocket 連接"""
        def on_message(ws, message):
            asyncio.create_task(self._handle_websocket_message(message))
        
        def on_error(ws, error):
            print(f"WebSocket error: {error}")
        
        def on_close(ws, close_status_code, close_msg):
            print("WebSocket connection closed")
            self.is_connected = False
        
        def on_open(ws):
            print("WebSocket connection established")
        
        self.ws_connection = websocket.WebSocketApp(
            self.websocket_url,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close,
            on_open=on_open
        )
        
        # 在單獨線程中運行 WebSocket
        self.ws_thread = threading.Thread(target=self.ws_connection.run_forever)
        self.ws_thread.daemon = True
        self.ws_thread.start()
    
    async def _inject_toolbar(self):
        """注入 Stagewise 工具欄"""
        toolbar_script = f"""
        // Stagewise Toolbar Injection Script
        (function() {{
            if (window.stagewise) {{
                return; // Already injected
            }}
            
            // Create toolbar container
            const toolbarContainer = document.createElement('div');
            toolbarContainer.id = 'stagewise-toolbar';
            toolbarContainer.style.cssText = `
                position: fixed;
                top: 10px;
                right: 10px;
                z-index: 999999;
                background: #2d3748;
                border-radius: 8px;
                padding: 12px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.3);
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                color: white;
                min-width: 200px;
            `;
            
            // Create toolbar content
            toolbarContainer.innerHTML = `
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                    <div style="width: 8px; height: 8px; background: #48bb78; border-radius: 50%;"></div>
                    <span style="font-size: 14px; font-weight: 600;">Stagewise Active</span>
                </div>
                <div style="display: flex; gap: 4px; flex-wrap: wrap;">
                    <button id="sw-select-mode" style="padding: 4px 8px; background: #4299e1; border: none; border-radius: 4px; color: white; font-size: 12px; cursor: pointer;">Select</button>
                    <button id="sw-inspect-mode" style="padding: 4px 8px; background: #9f7aea; border: none; border-radius: 4px; color: white; font-size: 12px; cursor: pointer;">Inspect</button>
                    <button id="sw-modify-mode" style="padding: 4px 8px; background: #ed8936; border: none; border-radius: 4px; color: white; font-size: 12px; cursor: pointer;">Modify</button>
                </div>
                <div id="sw-element-info" style="margin-top: 8px; font-size: 11px; color: #a0aec0; display: none;">
                    <div>Element: <span id="sw-element-tag"></span></div>
                    <div>Class: <span id="sw-element-class"></span></div>
                    <div>ID: <span id="sw-element-id"></span></div>
                </div>
            `;
            
            document.body.appendChild(toolbarContainer);
            
            // Initialize Stagewise functionality
            window.stagewise = {{
                mode: 'select',
                selectedElement: null,
                
                init: function() {{
                    this.bindEvents();
                    this.setupElementHighlighting();
                }},
                
                bindEvents: function() {{
                    document.getElementById('sw-select-mode').onclick = () => this.setMode('select');
                    document.getElementById('sw-inspect-mode').onclick = () => this.setMode('inspect');
                    document.getElementById('sw-modify-mode').onclick = () => this.setMode('modify');
                }},
                
                setMode: function(mode) {{
                    this.mode = mode;
                    document.querySelectorAll('#stagewise-toolbar button').forEach(btn => {{
                        btn.style.opacity = '0.6';
                    }});
                    document.getElementById('sw-' + mode + '-mode').style.opacity = '1';
                }},
                
                setupElementHighlighting: function() {{
                    let highlightOverlay = null;
                    
                    document.addEventListener('mouseover', (e) => {{
                        if (e.target.closest('#stagewise-toolbar')) return;
                        
                        // Remove existing highlight
                        if (highlightOverlay) {{
                            highlightOverlay.remove();
                        }}
                        
                        // Create new highlight
                        const rect = e.target.getBoundingClientRect();
                        highlightOverlay = document.createElement('div');
                        highlightOverlay.style.cssText = `
                            position: fixed;
                            top: ${{rect.top}}px;
                            left: ${{rect.left}}px;
                            width: ${{rect.width}}px;
                            height: ${{rect.height}}px;
                            border: 2px solid #4299e1;
                            background: rgba(66, 153, 225, 0.1);
                            pointer-events: none;
                            z-index: 999998;
                        `;
                        document.body.appendChild(highlightOverlay);
                    }});
                    
                    document.addEventListener('mouseout', () => {{
                        if (highlightOverlay) {{
                            highlightOverlay.remove();
                            highlightOverlay = null;
                        }}
                    }});
                    
                    document.addEventListener('click', (e) => {{
                        if (e.target.closest('#stagewise-toolbar')) return;
                        
                        e.preventDefault();
                        e.stopPropagation();
                        
                        this.selectElement(e.target);
                    }});
                }},
                
                selectElement: function(element) {{
                    this.selectedElement = element;
                    
                    // Update element info display
                    const infoDiv = document.getElementById('sw-element-info');
                    document.getElementById('sw-element-tag').textContent = element.tagName.toLowerCase();
                    document.getElementById('sw-element-class').textContent = element.className || 'none';
                    document.getElementById('sw-element-id').textContent = element.id || 'none';
                    infoDiv.style.display = 'block';
                    
                    // Send selection event
                    this.sendEvent('element_selected', {{
                        tagName: element.tagName,
                        className: element.className,
                        id: element.id,
                        textContent: element.textContent?.substring(0, 100),
                        attributes: Array.from(element.attributes).reduce((acc, attr) => {{
                            acc[attr.name] = attr.value;
                            return acc;
                        }}, {{}})
                    }});
                }},
                
                sendEvent: function(eventType, data) {{
                    // Send event to Python backend via WebSocket
                    if (window.stagewise_ws) {{
                        window.stagewise_ws.send(JSON.stringify({{
                            type: eventType,
                            data: data,
                            timestamp: Date.now()
                        }}));
                    }}
                }}
            }};
            
            // Initialize
            window.stagewise.init();
            
            // Establish WebSocket connection to Python backend
            try {{
                window.stagewise_ws = new WebSocket('ws://localhost:{self.toolbar_port}/stagewise');
                window.stagewise_ws.onopen = function() {{
                    console.log('Stagewise WebSocket connected');
                }};
                window.stagewise_ws.onmessage = function(event) {{
                    const message = JSON.parse(event.data);
                    window.stagewise.handleMessage(message);
                }};
            }} catch (e) {{
                console.warn('Could not connect to Stagewise WebSocket:', e);
            }}
        }})();
        """
        
        if self.driver:
            self.driver.execute_script(toolbar_script)
    
    async def _handle_websocket_message(self, message: str):
        """處理 WebSocket 消息"""
        try:
            data = json.loads(message)
            event_type = data.get('type')
            event_data = data.get('data', {})
            
            if event_type == 'element_selected':
                await self._handle_element_selection(event_data)
            elif event_type == 'element_modified':
                await self._handle_element_modification(event_data)
            elif event_type == 'inspection_request':
                await self._handle_inspection_request(event_data)
                
        except json.JSONDecodeError as e:
            print(f"Invalid WebSocket message: {e}")
    
    async def _handle_element_selection(self, element_data: Dict[str, Any]):
        """處理元素選擇事件"""
        
        # 創建可視化調試消息
        visual_debug_message = VisualDebugMessage(
            source='stagewise',
            session_id=self.config.get('session_id'),
            user_id=self.config.get('user_id', 'developer'),
            element_id=element_data.get('id', ''),
            action='select',
            properties=element_data,
            dom_path=self._generate_dom_path(element_data)
        )
        
        # 觸發事件處理器
        handler = self.event_handlers.get('element_selected')
        if handler:
            await handler(visual_debug_message)
    
    async def _handle_element_modification(self, modification_data: Dict[str, Any]):
        """處理元素修改事件"""
        
        # 創建UI修改消息
        ui_modification_message = UIModificationMessage(
            source='stagewise',
            session_id=self.config.get('session_id'),
            user_id=self.config.get('user_id', 'developer'),
            modification_id=f"stagewise_{int(time.time())}",
            target_element=modification_data.get('element_id', ''),
            modification_type=modification_data.get('type', 'style'),
            parameters=modification_data.get('parameters', {})
        )
        
        # 觸發事件處理器
        handler = self.event_handlers.get('element_modified')
        if handler:
            await handler(ui_modification_message)
    
    async def _handle_inspection_request(self, inspection_data: Dict[str, Any]):
        """處理元素檢查請求"""
        
        element_id = inspection_data.get('element_id')
        if not element_id:
            return
        
        # 執行詳細檢查
        inspection_result = await self._perform_element_inspection(element_id)
        
        # 發送檢查結果
        if self.ws_connection:
            response = {
                'type': 'inspection_result',
                'element_id': element_id,
                'result': inspection_result
            }
            self.ws_connection.send(json.dumps(response))
    
    async def _perform_element_inspection(self, element_id: str) -> Dict[str, Any]:
        """執行元素詳細檢查"""
        
        if not self.driver:
            return {}
        
        try:
            # 查找元素
            element = self.driver.find_element(By.ID, element_id)
            
            # 獲取計算樣式
            computed_styles = self.driver.execute_script("""
                const element = arguments[0];
                const styles = window.getComputedStyle(element);
                const result = {};
                for (let i = 0; i < styles.length; i++) {
                    const property = styles[i];
                    result[property] = styles.getPropertyValue(property);
                }
                return result;
            """, element)
            
            # 獲取元素信息
            element_info = {
                'tag_name': element.tag_name,
                'text': element.text,
                'attributes': {attr: element.get_attribute(attr) for attr in element.get_property('attributes')},
                'computed_styles': computed_styles,
                'bounding_rect': element.rect,
                'is_displayed': element.is_displayed(),
                'is_enabled': element.is_enabled()
            }
            
            # 可訪問性檢查
            accessibility_info = await self._check_accessibility(element)
            element_info['accessibility'] = accessibility_info
            
            # 性能分析
            performance_info = await self._analyze_performance(element)
            element_info['performance'] = performance_info
            
            return element_info
            
        except Exception as e:
            return {'error': str(e)}
    
    async def _check_accessibility(self, element) -> Dict[str, Any]:
        """檢查元素可訪問性"""
        
        accessibility_issues = []
        
        # 檢查 alt 屬性
        if element.tag_name.lower() == 'img' and not element.get_attribute('alt'):
            accessibility_issues.append({
                'type': 'missing_alt',
                'severity': 'high',
                'message': 'Image missing alt attribute'
            })
        
        # 檢查顏色對比度
        bg_color = self.driver.execute_script("""
            const element = arguments[0];
            const styles = window.getComputedStyle(element);
            return {
                color: styles.color,
                backgroundColor: styles.backgroundColor
            };
        """, element)
        
        # 檢查鍵盤可訪問性
        if element.tag_name.lower() in ['button', 'a', 'input'] and not element.get_attribute('tabindex'):
            tabindex = element.get_attribute('tabindex')
            if tabindex and int(tabindex) < 0:
                accessibility_issues.append({
                    'type': 'keyboard_inaccessible',
                    'severity': 'medium',
                    'message': 'Element not keyboard accessible'
                })
        
        return {
            'issues': accessibility_issues,
            'score': max(0, 100 - len(accessibility_issues) * 20)
        }
    
    async def _analyze_performance(self, element) -> Dict[str, Any]:
        """分析元素性能"""
        
        performance_metrics = self.driver.execute_script("""
            const element = arguments[0];
            const rect = element.getBoundingClientRect();
            
            // 檢查是否在視口內
            const isInViewport = (
                rect.top >= 0 &&
                rect.left >= 0 &&
                rect.bottom <= window.innerHeight &&
                rect.right <= window.innerWidth
            );
            
            // 檢查元素大小
            const area = rect.width * rect.height;
            
            return {
                isInViewport: isInViewport,
                area: area,
                width: rect.width,
                height: rect.height,
                position: {
                    top: rect.top,
                    left: rect.left
                }
            };
        """, element)
        
        return performance_metrics
    
    def _generate_dom_path(self, element_data: Dict[str, Any]) -> str:
        """生成 DOM 路徑"""
        
        tag_name = element_data.get('tagName', '').lower()
        element_id = element_data.get('id', '')
        class_name = element_data.get('className', '')
        
        path_parts = [tag_name]
        
        if element_id:
            path_parts.append(f'#{element_id}')
        elif class_name:
            # 取第一個類名
            first_class = class_name.split()[0] if class_name else ''
            if first_class:
                path_parts.append(f'.{first_class}')
        
        return ''.join(path_parts)
    
    def register_event_handler(self, event_type: str, handler: Callable):
        """註冊事件處理器"""
        self.event_handlers[event_type] = handler
    
    async def navigate_to_url(self, url: str):
        """導航到指定 URL"""
        if self.driver:
            self.driver.get(url)
            
            # 重新注入工具欄
            if self.auto_inject:
                await asyncio.sleep(1)  # 等待頁面載入
                await self._inject_toolbar()
    
    async def take_screenshot(self) -> str:
        """截取頁面截圖"""
        if self.driver:
            screenshot = self.driver.get_screenshot_as_png()
            return base64.b64encode(screenshot).decode('utf-8')
        return ""
    
    async def execute_modification(self, modification: UIModificationMessage) -> bool:
        """執行UI修改"""
        
        if not self.driver:
            return False
        
        try:
            target_element = modification.payload.get('target_element')
            modification_type = modification.payload.get('modification_type')
            parameters = modification.payload.get('parameters', {})
            
            # 查找目標元素
            element = self.driver.find_element(By.CSS_SELECTOR, target_element)
            
            if modification_type == 'style':
                # 修改樣式
                styles = parameters.get('styles', {})
                for property_name, value in styles.items():
                    self.driver.execute_script(
                        f"arguments[0].style.{property_name} = arguments[1];",
                        element, value
                    )
            
            elif modification_type == 'content':
                # 修改內容
                new_content = parameters.get('content', '')
                self.driver.execute_script(
                    "arguments[0].textContent = arguments[1];",
                    element, new_content
                )
            
            elif modification_type == 'attribute':
                # 修改屬性
                attributes = parameters.get('attributes', {})
                for attr_name, attr_value in attributes.items():
                    element.set_attribute(attr_name, attr_value)
            
            return True
            
        except Exception as e:
            print(f"Failed to execute modification: {e}")
            return False
    
    async def cleanup(self):
        """清理資源"""
        
        if self.ws_connection:
            self.ws_connection.close()
        
        if self.ws_thread and self.ws_thread.is_alive():
            self.ws_thread.join(timeout=5)
        
        if self.driver:
            self.driver.quit()
        
        self.is_connected = False


# 工具函數
def create_stagewise_integration(config: Dict[str, Any]) -> StagewiseIntegration:
    """創建 Stagewise 整合實例"""
    return StagewiseIntegration(config)


# 導出
__all__ = ['StagewiseIntegration', 'create_stagewise_integration']

