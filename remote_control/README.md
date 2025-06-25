# SmartUI Fusion 遠端控制方案

## 🎯 概述

這是一個完整的 EC2 到 Mac 遠端控制解決方案，用於自動化 VS Code 擴展的開發、構建和部署流程。

## 🏗️ 系統架構

```
┌─────────────────┐    VPN Tunnel    ┌─────────────────┐
│      EC2        │ ←──────────────→ │      Mac        │
│                 │                  │                 │
│ ┌─────────────┐ │    SSH/SCP       │ ┌─────────────┐ │
│ │ Development │ │ ←──────────────→ │ │   VS Code   │ │
│ │ Environment │ │                  │ │ Extensions  │ │
│ └─────────────┘ │                  │ └─────────────┘ │
│                 │                  │                 │
│ ┌─────────────┐ │    Automation    │ ┌─────────────┐ │
│ │ Build &     │ │ ←──────────────→ │ │ Auto Deploy │ │
│ │ Deploy      │ │                  │ │ Service     │ │
│ └─────────────┘ │                  │ └─────────────┘ │
└─────────────────┘                  └─────────────────┘
```

## 🚀 快速開始

### 1. Mac 端設置 (一次性)

```bash
# 複製配置腳本到 Mac
scp ec2_remote_via_vpn:/path/to/mac_ssh_setup.sh ~/mac_ssh_setup.sh

# 執行配置
chmod +x ~/mac_ssh_setup.sh
~/mac_ssh_setup.sh

# 啟動守護進程
~/vsix_deploy/remote_deploy_handler.sh --daemon
```

### 2. EC2 端使用

```bash
# 交互式界面
./start_powerautomation_mcp.sh

# 直接部署
./auto_deploy_vsix.sh

# 系統測試
./execute_powerautomation_startup.sh
```

## 📁 核心文件說明

### 主要腳本

- **`mac_ssh_setup.sh`** - Mac 端一次性配置腳本
- **`auto_deploy_vsix.sh`** - EC2 端主要部署腳本
- **`start_powerautomation_mcp.sh`** - 交互式操作界面
- **`execute_powerautomation_startup.sh`** - 系統測試腳本

### 配置文件

- **`quick_start_commands.txt`** - 完整使用指南
- **`README.md`** - 本文檔

## 🔧 功能特性

### ✅ 自動化構建
- 從源碼自動構建 VS Code 擴展
- TypeScript 編譯和依賴管理
- VSIX 打包和版本控制

### ✅ 遠端部署
- 通過 VPN 和 SSH 安全傳輸
- 自動文件傳輸和權限設置
- 錯誤處理和重試機制

### ✅ 智能安裝
- 自動卸載舊版本擴展
- 新版本安裝和驗證
- 備份和回滾功能

### ✅ 狀態監控
- 實時部署狀態監控
- 詳細的日誌記錄
- 系統健康檢查

## 🔗 網絡配置

### SSH 配置示例
```
Host ec2_remote_via_vpn
    Hostname 18.212.97.173
    Port 22
    User ec2-user
    IdentityFile /path/to/key.pem
    ProxyCommand socat STDIO SOCKS5:127.0.0.1:7897:%h:%p
```

### 安全考量
- SSH 密鑰認證
- VPN 加密隧道
- 最小權限原則
- 操作日誌記錄

## 🛠️ 故障排除

### 常見問題

1. **SSH 連接失敗**
   - 檢查 VPN 連接狀態
   - 確認 SOCKS5 代理運行
   - 驗證 SSH 密鑰權限

2. **VSIX 部署失敗**
   - 檢查 Mac 端守護進程
   - 確認 VS Code 命令行工具
   - 查看部署日誌

3. **文件傳輸問題**
   - 測試基本 SCP 功能
   - 檢查目錄權限
   - 確認網絡穩定性

### 調試命令

```bash
# 測試 SSH 連接
ssh -v ec2_remote_via_vpn

# 檢查 Mac 端狀態
./auto_deploy_vsix.sh --status

# 查看詳細日誌
ssh ec2_remote_via_vpn "tail -f ~/vsix_deploy/install.log"
```

## 📊 使用流程

1. **開發階段**
   - 在 EC2 修改 VS Code 擴展代碼
   - 本地測試和調試

2. **構建階段**
   - 執行自動化構建腳本
   - 生成 VSIX 擴展包

3. **部署階段**
   - 自動傳輸到 Mac 端
   - 觸發安裝流程

4. **測試階段**
   - 在 Mac 端 VS Code 測試
   - 收集使用反饋

5. **迭代優化**
   - 根據反饋調整代碼
   - 重複部署流程

## 🎉 成功標誌

- ✅ SSH 連接測試成功
- ✅ VSIX 文件能夠傳輸
- ✅ VS Code 擴展自動安裝
- ✅ 守護進程正常運行
- ✅ 日誌記錄完整

## 📞 技術支持

如遇問題，請檢查：
1. 網絡連接狀態
2. 配置文件正確性
3. 權限設置
4. 日誌錯誤信息

---

**SmartUI Fusion Remote Control System v1.0**  
*讓遠端開發變得簡單高效* 🚀

