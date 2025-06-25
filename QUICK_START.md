# SmartUI Fusion 快速開始指南

## 🎯 項目概述

SmartUI Fusion 是一個革命性的多模態智慧UI系統，整合了三個核心框架：
- **Stagewise** - 可視化調試和界面分析
- **LiveKit** - 語音交互和實時通信
- **AG-UI 協議** - 統一的通信標準
- **smartui_mcp** - 智能決策和用戶行為分析

## 🚀 快速開始

### 1. 本地開發環境

```bash
# 安裝依賴
pip install -r requirements.txt
npm install

# 啟動服務
./scripts/start.sh

# 訪問前端
http://localhost:8000
```

### 2. VS Code 擴展開發

```bash
# 進入 VS Code 擴展目錄
cd vscode-extension

# 安裝依賴
npm install

# 編譯
npm run compile

# 打包 VSIX
npx vsce package
```

### 3. 反向隧道部署（EC2 → Mac）

```bash
# 測試隧道連接
./remote_control/auto_deploy_vsix_tunnel.sh test

# 完整部署
./remote_control/auto_deploy_vsix_complete.sh
```

## 📁 項目結構

```
0625newfeature/
├── src/                          # 核心源代碼
│   ├── core/                     # 智能決策引擎
│   ├── integrations/             # 框架整合
│   └── protocols/                # AG-UI 協議
├── vscode-extension/             # VS Code 擴展
├── electron-app/                 # 桌面應用
├── android-app/                  # Android 應用
├── smartui-frontend-demo/        # React 前端示例
├── remote_control/               # 遠程部署腳本
├── config/                       # 配置文件
├── scripts/                      # 啟動腳本
└── docs/                         # 文檔

重要文件：
├── alexchuang.pem               # AWS EC2 私鑰
├── QUICK_START.md               # 本文件
└── README.md                    # 項目說明
```

## 🔧 常用命令

### 開發環境
```bash
# 啟動完整服務
python -m src.main

# 啟動前端開發服務器
cd smartui-frontend-demo && npm start

# 運行測試
python -m pytest tests/
```

### 部署相關
```bash
# 測試反向隧道
./remote_control/auto_deploy_vsix_tunnel.sh test

# 部署 VS Code 擴展
./remote_control/auto_deploy_vsix_complete.sh

# 檢查服務狀態
./scripts/check_status.sh
```

### Git 操作
```bash
# 提交更改
git add .
git commit -m "描述更改"
git push origin main

# 檢查狀態
git status
git log --oneline -10
```

## 🌐 服務端點

- **主服務**: http://localhost:8000
- **WebSocket**: ws://localhost:8000/ws
- **API 文檔**: http://localhost:8000/docs
- **前端示例**: http://localhost:3000

## 📋 前置條件

### 開發環境
- Python 3.11+
- Node.js 20+
- VS Code
- Git

### 部署環境
- AWS EC2 實例
- Mac 開發機器
- VPN 連接
- SSH 密鑰配置

## 🔐 安全配置

### SSH 密鑰
```bash
# 設置正確權限
chmod 600 alexchuang.pem

# 測試連接
ssh -i alexchuang.pem ec2-user@your-ec2-ip
```

### 環境變量
```bash
# 設置必要的環境變量
export AWS_REGION=us-east-1
export NODE_ENV=development
export PYTHONPATH=$PWD/src
```

## 🆘 故障排除

### 常見問題

1. **端口被占用**
   ```bash
   lsof -i :8000
   kill -9 <PID>
   ```

2. **依賴安裝失敗**
   ```bash
   pip install --upgrade pip
   npm cache clean --force
   ```

3. **反向隧道連接失敗**
   ```bash
   # 檢查 SSH 配置
   ssh -v ec2_remote_via_vpn
   
   # 重啟隧道
   pkill -f "ssh.*2222"
   ssh ec2_remote_via_vpn -R 2222:localhost:22 -N
   ```

## 📚 詳細文檔

- [開發指南](docs/DEVELOPMENT_GUIDE.md)
- [反向隧道部署](remote_control/TUNNEL_DEPLOYMENT_GUIDE.md)
- [API 參考](docs/API_REFERENCE.md)
- [架構設計](docs/ARCHITECTURE.md)

## 🎯 下一步

1. **本地測試** - 確保所有服務正常運行
2. **擴展開發** - 根據需求開發 VS Code 擴展功能
3. **部署測試** - 使用反向隧道進行遠程部署
4. **功能擴展** - 添加 LiveKit 語音交互功能

## 💡 提示

- 保持 Mac 端反向隧道連接穩定
- 定期備份重要配置和密鑰
- 使用 Git 管理代碼版本
- 查看日誌文件排查問題

---

**SmartUI Fusion** - 下一代智慧UI交互系統 🚀

