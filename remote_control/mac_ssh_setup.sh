#!/bin/bash

# Mac 端 SSH 服務配置腳本
# 用於啟用從 EC2 到 Mac 的反向連接

echo "🚀 配置 Mac 端 SSH 服務以支持 EC2 遠端控制..."

# 1. 啟用 SSH 服務
echo "📡 啟用 SSH 服務..."
sudo systemsetup -setremotelogin on

# 2. 檢查 SSH 服務狀態
echo "🔍 檢查 SSH 服務狀態..."
sudo systemsetup -getremotelogin

# 3. 創建專用的部署用戶（可選，使用現有用戶也可以）
echo "👤 配置部署用戶權限..."
# 獲取當前用戶
CURRENT_USER=$(whoami)
echo "當前用戶: $CURRENT_USER"

# 4. 設置 SSH 密鑰目錄權限
echo "🔐 設置 SSH 密鑰權限..."
mkdir -p ~/.ssh
chmod 700 ~/.ssh
touch ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys

# 5. 創建 VS Code 擴展部署目錄
echo "📁 創建 VS Code 擴展部署目錄..."
VSCODE_EXTENSIONS_DIR="$HOME/.vscode/extensions"
DEPLOY_DIR="$HOME/vsix_deploy"
mkdir -p "$DEPLOY_DIR"
mkdir -p "$VSCODE_EXTENSIONS_DIR"

echo "✅ VS Code 擴展目錄: $VSCODE_EXTENSIONS_DIR"
echo "✅ 部署工作目錄: $DEPLOY_DIR"

# 6. 創建自動安裝 VSIX 的腳本
echo "📦 創建 VSIX 自動安裝腳本..."
cat > "$DEPLOY_DIR/install_vsix.sh" << 'EOF'
#!/bin/bash

# VSIX 自動安裝腳本
VSIX_FILE="$1"
EXTENSION_NAME="$2"

if [ -z "$VSIX_FILE" ]; then
    echo "❌ 錯誤: 請提供 VSIX 文件路徑"
    echo "用法: $0 <vsix_file> [extension_name]"
    exit 1
fi

if [ ! -f "$VSIX_FILE" ]; then
    echo "❌ 錯誤: VSIX 文件不存在: $VSIX_FILE"
    exit 1
fi

echo "🔧 安裝 VSIX 擴展: $VSIX_FILE"

# 檢查 VS Code 是否安裝
if ! command -v code &> /dev/null; then
    echo "❌ 錯誤: VS Code 命令行工具未安裝"
    echo "請在 VS Code 中執行 'Shell Command: Install code command in PATH'"
    exit 1
fi

# 如果提供了擴展名，先卸載舊版本
if [ ! -z "$EXTENSION_NAME" ]; then
    echo "🗑️  卸載舊版本擴展: $EXTENSION_NAME"
    code --uninstall-extension "$EXTENSION_NAME" 2>/dev/null || true
fi

# 安裝新的 VSIX
echo "📦 安裝新的 VSIX 擴展..."
if code --install-extension "$VSIX_FILE"; then
    echo "✅ VSIX 擴展安裝成功!"
    
    # 記錄安裝日誌
    echo "$(date): 成功安裝 $VSIX_FILE" >> "$HOME/vsix_deploy/install.log"
    
    # 可選：重啟 VS Code（如果正在運行）
    echo "🔄 建議重啟 VS Code 以加載新擴展"
    
    return 0
else
    echo "❌ VSIX 擴展安裝失敗!"
    echo "$(date): 安裝失敗 $VSIX_FILE" >> "$HOME/vsix_deploy/install.log"
    return 1
fi
EOF

chmod +x "$DEPLOY_DIR/install_vsix.sh"

# 7. 創建遠端部署接收腳本
echo "📡 創建遠端部署接收腳本..."
cat > "$DEPLOY_DIR/remote_deploy_handler.sh" << 'EOF'
#!/bin/bash

# 遠端部署處理腳本
# 監聽來自 EC2 的部署請求

DEPLOY_DIR="$HOME/vsix_deploy"
INCOMING_DIR="$DEPLOY_DIR/incoming"
BACKUP_DIR="$DEPLOY_DIR/backup"

# 創建必要目錄
mkdir -p "$INCOMING_DIR" "$BACKUP_DIR"

echo "🎯 遠端部署處理器已啟動..."
echo "📁 監聽目錄: $INCOMING_DIR"

# 處理新到達的 VSIX 文件
process_vsix() {
    local vsix_file="$1"
    local filename=$(basename "$vsix_file")
    local extension_name="${filename%%-*}"  # 提取擴展名前綴
    
    echo "🔄 處理 VSIX 文件: $filename"
    
    # 備份現有擴展（如果存在）
    if [ -d "$HOME/.vscode/extensions/$extension_name"* ]; then
        echo "💾 備份現有擴展..."
        cp -r "$HOME/.vscode/extensions/$extension_name"* "$BACKUP_DIR/" 2>/dev/null || true
    fi
    
    # 安裝新擴展
    if "$DEPLOY_DIR/install_vsix.sh" "$vsix_file" "$extension_name"; then
        echo "✅ 部署成功: $filename"
        # 移動到已處理目錄
        mv "$vsix_file" "$DEPLOY_DIR/processed_$(date +%Y%m%d_%H%M%S)_$filename"
    else
        echo "❌ 部署失敗: $filename"
        # 移動到失敗目錄
        mkdir -p "$DEPLOY_DIR/failed"
        mv "$vsix_file" "$DEPLOY_DIR/failed/failed_$(date +%Y%m%d_%H%M%S)_$filename"
    fi
}

# 監聽新文件（簡單版本，實際可以用 fswatch 或 inotify）
monitor_incoming() {
    while true; do
        for vsix_file in "$INCOMING_DIR"/*.vsix; do
            if [ -f "$vsix_file" ]; then
                process_vsix "$vsix_file"
            fi
        done
        sleep 2
    done
}

# 如果作為守護進程運行
if [ "$1" = "--daemon" ]; then
    echo "🔄 以守護進程模式運行..."
    monitor_incoming &
    echo $! > "$DEPLOY_DIR/daemon.pid"
    echo "✅ 守護進程已啟動，PID: $(cat $DEPLOY_DIR/daemon.pid)"
else
    echo "💡 手動模式 - 處理現有文件..."
    for vsix_file in "$INCOMING_DIR"/*.vsix; do
        if [ -f "$vsix_file" ]; then
            process_vsix "$vsix_file"
        fi
    done
fi
EOF

chmod +x "$DEPLOY_DIR/remote_deploy_handler.sh"

# 8. 創建狀態檢查腳本
echo "📊 創建狀態檢查腳本..."
cat > "$DEPLOY_DIR/check_status.sh" << 'EOF'
#!/bin/bash

echo "🔍 Mac 端遠端控制狀態檢查"
echo "================================"

# SSH 服務狀態
echo "📡 SSH 服務狀態:"
sudo systemsetup -getremotelogin

# VS Code 安裝狀態
echo ""
echo "💻 VS Code 狀態:"
if command -v code &> /dev/null; then
    echo "✅ VS Code 命令行工具已安裝"
    code --version | head -1
else
    echo "❌ VS Code 命令行工具未安裝"
fi

# 擴展目錄
echo ""
echo "📁 VS Code 擴展目錄:"
ls -la "$HOME/.vscode/extensions/" | head -5

# 部署目錄狀態
echo ""
echo "📦 部署目錄狀態:"
ls -la "$HOME/vsix_deploy/"

# 網絡連接測試
echo ""
echo "🌐 網絡連接測試:"
echo "本機 IP 地址:"
ifconfig | grep "inet " | grep -v 127.0.0.1

# 守護進程狀態
echo ""
echo "🔄 守護進程狀態:"
if [ -f "$HOME/vsix_deploy/daemon.pid" ]; then
    PID=$(cat "$HOME/vsix_deploy/daemon.pid")
    if ps -p $PID > /dev/null; then
        echo "✅ 守護進程運行中 (PID: $PID)"
    else
        echo "❌ 守護進程未運行"
    fi
else
    echo "❌ 守護進程未啟動"
fi
EOF

chmod +x "$DEPLOY_DIR/check_status.sh"

# 9. 顯示配置摘要
echo ""
echo "🎉 Mac 端配置完成!"
echo "================================"
echo "📁 部署目錄: $DEPLOY_DIR"
echo "📦 VSIX 安裝腳本: $DEPLOY_DIR/install_vsix.sh"
echo "📡 遠端處理腳本: $DEPLOY_DIR/remote_deploy_handler.sh"
echo "📊 狀態檢查腳本: $DEPLOY_DIR/check_status.sh"
echo ""
echo "🔧 下一步操作:"
echo "1. 啟動守護進程: $DEPLOY_DIR/remote_deploy_handler.sh --daemon"
echo "2. 檢查狀態: $DEPLOY_DIR/check_status.sh"
echo "3. 測試安裝: $DEPLOY_DIR/install_vsix.sh <vsix_file>"
echo ""
echo "✅ 現在可以從 EC2 遠端部署 VSIX 擴展了!"

