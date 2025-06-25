#!/bin/bash

# PowerAutomation VSIX 自動部署腳本
# 目標: 將 VSIX 檔案部署到 18.212.97.173 服務器

set -e

echo "🚀 開始 PowerAutomation VSIX 部署..."

# 配置變數
SOURCE_SERVER="52.201.232.178"
TARGET_SERVER="18.212.97.173"
VSIX_FILE="powerautomation-local-mcp-3.0.0.vsix"
SSH_ALIAS="ec2_remote_via_vpn"

# 步驟1: 下載 VSIX 檔案到本地
echo "📥 步驟1: 下載 VSIX 檔案..."
curl -o ~/Downloads/${VSIX_FILE} http://${SOURCE_SERVER}:8000/${VSIX_FILE}

if [ $? -eq 0 ]; then
    echo "✅ 檔案下載成功: ~/Downloads/${VSIX_FILE}"
else
    echo "❌ 檔案下載失敗"
    exit 1
fi

# 步驟2: 上傳到目標服務器
echo "📤 步驟2: 上傳到目標服務器..."
scp ~/Downloads/${VSIX_FILE} ${SSH_ALIAS}:/home/ec2-user/

if [ $? -eq 0 ]; then
    echo "✅ 檔案上傳成功"
else
    echo "❌ 檔案上傳失敗"
    exit 1
fi

# 步驟3: 在目標服務器上設置 HTTP 服務
echo "🌐 步驟3: 設置 HTTP 服務..."
ssh ${SSH_ALIAS} "cd /home/ec2-user && pkill -f 'python3 -m http.server' 2>/dev/null || true"
ssh ${SSH_ALIAS} "cd /home/ec2-user && nohup python3 -m http.server 8000 > http_server.log 2>&1 &"

if [ $? -eq 0 ]; then
    echo "✅ HTTP 服務啟動成功"
else
    echo "❌ HTTP 服務啟動失敗"
    exit 1
fi

# 步驟4: 驗證部署
echo "🔍 步驟4: 驗證部署..."
sleep 3
curl -I http://${TARGET_SERVER}:8000/${VSIX_FILE} 2>/dev/null | head -1

echo ""
echo "🎉 部署完成！"
echo "📁 VSIX 檔案現在可以從以下位置下載:"
echo "   http://${TARGET_SERVER}:8000/${VSIX_FILE}"
echo ""
echo "🔧 在 VS Code 中安裝:"
echo "   1. 下載檔案: curl -o ~/Downloads/${VSIX_FILE} http://${TARGET_SERVER}:8000/${VSIX_FILE}"
echo "   2. 安裝擴展: code --install-extension ~/Downloads/${VSIX_FILE}"
echo ""
echo "📞 如需協助修正或更新，請聯繫 Manus AI"

