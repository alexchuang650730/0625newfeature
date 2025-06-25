# SmartUI Fusion 開發指南

## 🎯 項目概述

SmartUI Fusion 是一個革命性的多模態智慧UI整合項目，將三個核心框架深度整合：

- **Stagewise**: 前端可視化調試工具
- **LiveKit**: 語音AI交互框架  
- **AG-UI Protocol**: 統一通信協議
- **smartui_mcp**: 智能決策引擎

## 🏗️ 架構設計

### 分層架構

```
┌─────────────────────────────────────────────────────────────┐
│                    用戶交互層                                │
│  Stagewise 可視化工具 │ LiveKit 語音交互 │ Web UI 界面      │
├─────────────────────────────────────────────────────────────┤
│                    智能決策層                                │
│              smartui_mcp 決策引擎整合                       │
├─────────────────────────────────────────────────────────────┤
│                    通信協調層                                │
│                AG-UI 協議標準化                             │
├─────────────────────────────────────────────────────────────┤
│                    服務執行層                                │
│        各框架核心服務和功能模塊                              │
├─────────────────────────────────────────────────────────────┤
│                    基礎設施層                                │
│      數據存儲、網絡通信、安全認證                            │
└─────────────────────────────────────────────────────────────┘
```

### 核心組件

#### 1. AG-UI 協議 (`src/protocols/ag_ui_protocol.py`)

統一的通信協議，定義了所有組件間的消息格式和交互規範。

**主要消息類型**：
- `VoiceCommandMessage`: 語音指令消息
- `VisualDebugMessage`: 可視化調試消息
- `UIModificationMessage`: UI修改消息
- `StateSyncMessage`: 狀態同步消息
- `UserInteractionMessage`: 用戶交互消息

**使用示例**：
```python
from src.protocols.ag_ui_protocol import VoiceCommandMessage

# 創建語音指令消息
voice_msg = VoiceCommandMessage(
    source='voice_client',
    session_id='session_123',
    user_id='user_456',
    transcript='修改按鈕顏色為藍色',
    intent={'action': 'modify', 'target': 'button', 'property': 'color', 'value': 'blue'},
    confidence=0.85
)
```

#### 2. 智能決策引擎 (`src/core/decision_engine.py`)

核心AI決策系統，負責理解用戶意圖並生成相應的UI操作指令。

**決策策略**：
- `RULE_BASED`: 基於規則的決策
- `ML_BASED`: 基於機器學習的決策
- `HYBRID`: 混合決策策略（推薦）
- `HEURISTIC`: 基於啟發式的決策

**使用示例**：
```python
from src.core.decision_engine import SmartUIDecisionEngine

# 初始化決策引擎
engine = SmartUIDecisionEngine({
    'strategy': 'hybrid',
    'confidence_threshold': 0.7,
    'learning_enabled': True
})

# 處理語音指令
ui_modification = await engine.process_voice_command(voice_message)
```

#### 3. Stagewise 整合 (`src/integrations/stagewise_integration.py`)

與 Stagewise 可視化調試工具的深度整合，提供實時的界面操作和調試功能。

**核心功能**：
- 自動注入可視化工具欄
- 實時元素選擇和高亮
- 智能界面分析和建議
- 可訪問性檢查
- 性能分析

**使用示例**：
```python
from src.integrations.stagewise_integration import StagewiseIntegration

# 初始化 Stagewise 整合
stagewise = StagewiseIntegration({
    'toolbar_port': 3001,
    'debug_mode': True,
    'auto_inject': True
})

# 導航到頁面並注入工具欄
await stagewise.navigate_to_url('https://example.com')
```

## 🚀 快速開始

### 1. 環境準備

**系統要求**：
- Python 3.11+
- Node.js 18+
- Chrome/Chromium 瀏覽器

**安裝依賴**：
```bash
# 克隆項目
git clone https://github.com/alexchuang650730/0625newfeature.git
cd 0625newfeature

# 安裝 Python 依賴
pip install -r requirements.txt

# 安裝 Node.js 依賴
npm install
```

### 2. 配置設置

編輯 `config/app_config.json` 文件：

```json
{
  "app": {
    "host": "0.0.0.0",
    "port": 8000,
    "debug": true
  },
  "decision_engine": {
    "strategy": "hybrid",
    "confidence_threshold": 0.7
  },
  "stagewise": {
    "toolbar_port": 3001,
    "auto_inject": true,
    "headless": false
  }
}
```

### 3. 啟動服務

```bash
# 使用啟動腳本（推薦）
./scripts/start.sh

# 或手動啟動
npm run dev
```

### 4. 驗證安裝

訪問以下URL確認服務正常運行：

- 前端界面: http://localhost:5173
- 後端API: http://localhost:8000
- API文檔: http://localhost:8000/docs
- 健康檢查: http://localhost:8000/health

## 🛠️ 開發工作流

### 1. 添加新的消息類型

1. 在 `src/protocols/ag_ui_protocol.py` 中定義新的消息類：

```python
class CustomMessage(AGUIMessage):
    message_type: MessageType = MessageType.CUSTOM
    
    def __init__(self, **data):
        super().__init__(**data)
        self.payload.update({
            'custom_field': data.get('custom_field', ''),
            # 添加其他字段
        })
```

2. 在決策引擎中添加處理邏輯：

```python
async def process_custom_message(self, message: CustomMessage) -> Optional[AGUIMessage]:
    # 實現處理邏輯
    pass
```

3. 註冊消息處理器：

```python
self.protocol_handler.register_handler(
    MessageType.CUSTOM,
    self._handle_custom_message
)
```

### 2. 擴展決策策略

1. 創建新的決策引擎類：

```python
class CustomDecisionEngine:
    async def decide(self, context: DecisionContext, input_data: Dict[str, Any]) -> DecisionResult:
        # 實現自定義決策邏輯
        pass
```

2. 在主決策引擎中集成：

```python
self.custom_engine = CustomDecisionEngine(config.get('custom_config', {}))
```

### 3. 添加新的整合模塊

1. 創建整合模塊文件 `src/integrations/new_integration.py`：

```python
class NewIntegration:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    async def initialize(self) -> bool:
        # 初始化邏輯
        pass
    
    async def cleanup(self):
        # 清理邏輯
        pass
```

2. 在主應用中註冊：

```python
self.new_integration = NewIntegration(self.config.get('new_integration', {}))
```

## 🧪 測試指南

### 單元測試

```bash
# 運行所有測試
pytest tests/

# 運行特定測試文件
pytest tests/test_decision_engine.py

# 運行測試並生成覆蓋率報告
pytest --cov=src tests/
```

### 集成測試

```bash
# 啟動測試環境
./scripts/start_test_env.sh

# 運行集成測試
pytest tests/integration/

# 停止測試環境
./scripts/stop_test_env.sh
```

### 手動測試

1. **語音交互測試**：
   - 啟動服務
   - 打開瀏覽器到測試頁面
   - 使用語音指令測試UI操作

2. **可視化調試測試**：
   - 導航到目標網頁
   - 使用 Stagewise 工具欄選擇元素
   - 驗證智能建議和分析結果

3. **協議通信測試**：
   - 使用 WebSocket 客戶端
   - 發送各種類型的消息
   - 驗證響應和狀態同步

## 📊 性能監控

### 內建指標

系統提供多種性能指標：

```python
# 獲取決策引擎性能指標
metrics = await decision_engine.get_performance_metrics()

# 指標包括：
# - total_decisions: 總決策次數
# - successful_decisions: 成功決策次數
# - average_confidence: 平均置信度
# - average_response_time: 平均響應時間
```

### 監控端點

- `/api/metrics`: 獲取系統性能指標
- `/health`: 健康檢查
- `/api/stats`: 詳細統計信息

## 🔧 故障排除

### 常見問題

1. **WebDriver 啟動失敗**：
   ```bash
   # 檢查 Chrome 是否安裝
   google-chrome --version
   
   # 安裝 ChromeDriver
   npm install -g chromedriver
   ```

2. **WebSocket 連接失敗**：
   - 檢查防火牆設置
   - 確認端口未被占用
   - 檢查 CORS 配置

3. **依賴安裝問題**：
   ```bash
   # 清理緩存
   pip cache purge
   npm cache clean --force
   
   # 重新安裝
   pip install -r requirements.txt --force-reinstall
   npm install --force
   ```

### 日誌分析

```bash
# 查看實時日誌
tail -f logs/smartui_fusion.log

# 搜索錯誤
grep "ERROR" logs/smartui_fusion.log

# 分析性能
grep "response_time" logs/smartui_fusion.log
```

## 🚀 部署指南

### 開發環境

使用提供的啟動腳本：

```bash
./scripts/start.sh
```

### 生產環境

1. **使用 Docker**：

```dockerfile
# Dockerfile 示例
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["python", "-m", "src.main"]
```

2. **使用 systemd**：

```ini
# /etc/systemd/system/smartui-fusion.service
[Unit]
Description=SmartUI Fusion Service
After=network.target

[Service]
Type=simple
User=smartui
WorkingDirectory=/opt/smartui-fusion
ExecStart=/opt/smartui-fusion/venv/bin/python -m src.main
Restart=always

[Install]
WantedBy=multi-user.target
```

### 雲端部署

支持部署到各種雲平台：

- **AWS**: 使用 ECS 或 Lambda
- **Google Cloud**: 使用 Cloud Run 或 GKE
- **Azure**: 使用 Container Instances 或 AKS
- **Heroku**: 直接部署

## 📚 API 參考

### WebSocket API

**連接端點**: `ws://localhost:8000/ws`

**消息格式**:
```json
{
  "message_id": "uuid",
  "message_type": "voice_command",
  "timestamp": "2025-06-25T10:00:00Z",
  "source": "client",
  "payload": {
    "transcript": "修改按鈕顏色",
    "intent": {...},
    "confidence": 0.85
  }
}
```

### REST API

**基礎端點**: `http://localhost:8000`

- `GET /`: 服務信息
- `GET /health`: 健康檢查
- `POST /api/navigate`: 導航到URL
- `GET /api/screenshot`: 截取頁面截圖
- `GET /api/metrics`: 性能指標

## 🤝 貢獻指南

### 開發流程

1. Fork 項目
2. 創建功能分支: `git checkout -b feature/new-feature`
3. 提交更改: `git commit -am 'Add new feature'`
4. 推送分支: `git push origin feature/new-feature`
5. 創建 Pull Request

### 代碼規範

- 使用 Black 進行代碼格式化
- 遵循 PEP 8 規範
- 添加類型註解
- 編寫單元測試
- 更新文檔

### 提交規範

使用 Conventional Commits 格式：

```
feat: 添加新功能
fix: 修復bug
docs: 更新文檔
style: 代碼格式調整
refactor: 代碼重構
test: 添加測試
chore: 構建過程或輔助工具的變動
```

## 📄 許可證

本項目採用 MIT 許可證。詳見 [LICENSE](../LICENSE) 文件。

## 🆘 支持

- 📧 Email: support@smartui-fusion.com
- 💬 Discord: [加入我們的社區](https://discord.gg/smartui-fusion)
- 📖 文檔: [完整文檔](https://docs.smartui-fusion.com)
- 🐛 問題反饋: [GitHub Issues](https://github.com/alexchuang650730/0625newfeature/issues)

---

**建立技術護城河，引領UI交互革命！** 🚀

