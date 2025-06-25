# SmartUI Fusion 反向隧道部署指南

## 🎯 概述

本指南說明如何通過 SSH 反向隧道從 EC2 自動部署 VS Code 擴展到 Mac 端。

## 🏗️ 架構圖

```
Mac (VPN) ←→ SSH Tunnel ←→ EC2 (AWS)
     ↓                        ↑
  VS Code                 構建 VSIX
     ↓                        ↑
自動安裝 ←←←← 反向隧道傳輸 ←←←←
```

## 📋 前置條件

### Mac 端要求
- ✅ SSH 服務已啟用
- ✅ VS Code 已安裝
- ✅ VPN 連接正常
- ✅ 守護進程運行中

### EC2 端要求
- ✅ Node.js 和 npm 已安裝
- ✅ SSH 配置支持反向隧道
- ✅ 項目代碼已部署

## 🚀 快速開始

### 1. Mac 端設置

```bash
# 啟用 SSH 服務
sudo systemsetup -setremotelogin on

# 啟動守護進程
/Users/alexchuang/vsix_deploy/remote_deploy_handler.sh --daemon

# 建立反向隧道
ssh ec2_remote_via_vpn -R 2222:localhost:22 -N -o ServerAliveInterval=30
```

### 2. EC2 端部署

```bash
# 進入項目目錄
cd /home/ec2-user/mytest/test/0625newfeature/remote_control

# 測試連接
./auto_deploy_vsix_tunnel.sh test

# 執行完整部署
./auto_deploy_vsix_complete.sh
```

## 📁 腳本說明

### auto_deploy_vsix_tunnel.sh
- **功能**: 測試反向隧道連接
- **用途**: 診斷連接問題
- **命令**: `./auto_deploy_vsix_tunnel.sh test`

### auto_deploy_vsix_complete.sh
- **功能**: 完整的 VSIX 構建和部署
- **流程**: 構建 → 打包 → 傳輸 → 安裝
- **命令**: `./auto_deploy_vsix_complete.sh`

## 🔧 故障排除

### 連接問題
```bash
# 檢查隧道狀態
netstat -tlnp | grep 2222

# 測試 SSH 連接
ssh -p 2222 alexchuang@localhost "echo test"
```

### 構建問題
```bash
# 檢查 Node.js 版本
node --version
npm --version

# 手動安裝 vsce
npm install -g vsce
```

### Mac 端問題
```bash
# 檢查守護進程
ps aux | grep remote_deploy_handler

# 檢查部署目錄
ls -la /Users/alexchuang/vsix_deploy/
```

## 📊 部署流程

1. **連接檢查** - 驗證反向隧道正常
2. **環境準備** - 創建構建目錄和項目結構
3. **依賴安裝** - npm install 和 TypeScript 編譯
4. **VSIX 打包** - 使用 vsce 打包擴展
5. **文件傳輸** - SCP 傳輸到 Mac 端
6. **自動安裝** - 觸發 Mac 端安裝腳本
7. **清理完成** - 清理臨時文件

## 🎉 成功標誌

- ✅ 隧道連接測試成功
- ✅ VSIX 文件構建完成
- ✅ 文件傳輸到 Mac 成功
- ✅ VS Code 擴展安裝成功
- ✅ 可以在 VS Code 中看到新擴展

## 🔄 日常使用

```bash
# 每次開發後部署
./auto_deploy_vsix_complete.sh

# 僅測試連接
./auto_deploy_vsix_tunnel.sh test

# 檢查 Mac 端狀態
ssh -p 2222 alexchuang@localhost "/Users/alexchuang/vsix_deploy/check_status.sh"
```

## 📝 注意事項

- 保持 Mac 端反向隧道連接
- 確保 Mac 端守護進程運行
- 部署時需要輸入 Mac 用戶密碼
- VS Code 需要重新加載窗口以使用新擴展

## 🔐 SSH 配置

### EC2 端 SSH 配置
```bash
# 編輯 SSH 配置
sudo vi /etc/ssh/sshd_config

# 確保有這些設置：
AllowTcpForwarding yes
GatewayPorts yes

# 重啟 SSH 服務
sudo systemctl restart sshd
```

### Mac 端 SSH 配置
```bash
# 編輯 SSH 配置
vi ~/.ssh/config

# 添加保活設置：
Host ec2_remote_via_vpn
    ServerAliveInterval 30
    ServerAliveCountMax 3
    TCPKeepAlive yes
```

## 🛠️ 自動重連腳本

```bash
# 創建自動重連腳本
cat > ~/tunnel_keeper.sh << 'EOF'
#!/bin/bash
while true; do
    echo "$(date): 啟動反向隧道..."
    ssh ec2_remote_via_vpn -R 2222:localhost:22 -N
    echo "$(date): 隧道斷開，5秒後重連..."
    sleep 5
done
EOF

chmod +x ~/tunnel_keeper.sh
# 執行
~/tunnel_keeper.sh
```

