#!/bin/bash

# SmartUI Fusion 完整 VSIX 部署腳本
set -e

# 配置變量
MAC_HOST="localhost"
MAC_PORT="2222"
MAC_USER="alexchuang"
MAC_DEPLOY_DIR="/Users/$MAC_USER/vsix_deploy"
LOCAL_BUILD_DIR="/tmp/vsix_build"

# 動態檢測項目目錄
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# 顏色輸出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 檢查連接
check_connection() {
    log_info "檢查反向隧道連接..."
    
    if ! netstat -tlnp 2>/dev/null | grep ":$MAC_PORT" > /dev/null; then
        log_error "反向隧道端口 $MAC_PORT 未監聽"
        log_info "請在 Mac 端執行: ssh ec2_remote_via_vpn -R 2222:localhost:22 -N"
        return 1
    fi
    
    if ! ssh -p $MAC_PORT -o ConnectTimeout=5 -o BatchMode=yes $MAC_USER@$MAC_HOST "echo test" 2>/dev/null; then
        log_warning "需要密碼認證，將在傳輸時提示輸入"
    fi
    
    log_success "連接檢查完成"
    return 0
}

# 準備構建環境
prepare_build() {
    log_info "準備構建環境..."
    
    rm -rf "$LOCAL_BUILD_DIR"
    mkdir -p "$LOCAL_BUILD_DIR"
    
    # 檢查或創建 VS Code 擴展項目
    if [[ ! -d "$PROJECT_DIR/vscode-extension" ]]; then
        log_info "創建 VS Code 擴展項目..."
        mkdir -p "$PROJECT_DIR/vscode-extension/src"
        
        # 創建 package.json
        cat > "$PROJECT_DIR/vscode-extension/package.json" << 'PACKAGE_EOF'
{
  "name": "smartui-fusion-vscode",
  "displayName": "SmartUI Fusion",
  "description": "SmartUI Fusion VS Code Extension - Remote Deployed",
  "version": "1.0.0",
  "engines": { "vscode": "^1.74.0" },
  "categories": ["Other"],
  "activationEvents": [],
  "main": "./out/extension.js",
  "contributes": {
    "commands": [
      {
        "command": "smartui-fusion.helloWorld",
        "title": "SmartUI Fusion: Hello World"
      },
      {
        "command": "smartui-fusion.deployStatus",
        "title": "SmartUI Fusion: Deploy Status"
      }
    ]
  },
  "scripts": {
    "compile": "tsc -p ./",
    "watch": "tsc -watch -p ./"
  },
  "devDependencies": {
    "@types/vscode": "^1.74.0",
    "@types/node": "16.x",
    "typescript": "^4.9.4"
  }
}
PACKAGE_EOF
        
        # 創建 tsconfig.json
        cat > "$PROJECT_DIR/vscode-extension/tsconfig.json" << 'TSCONFIG_EOF'
{
  "compilerOptions": {
    "module": "commonjs",
    "target": "ES2020",
    "outDir": "out",
    "lib": ["ES2020"],
    "sourceMap": true,
    "rootDir": "src",
    "strict": true
  }
}
TSCONFIG_EOF
        
        # 創建擴展主文件
        cat > "$PROJECT_DIR/vscode-extension/src/extension.ts" << 'EXTENSION_EOF'
import * as vscode from 'vscode';

export function activate(context: vscode.ExtensionContext) {
    console.log('SmartUI Fusion extension activated via EC2 remote deployment! 🚀');
    
    let helloWorld = vscode.commands.registerCommand('smartui-fusion.helloWorld', () => {
        vscode.window.showInformationMessage('Hello from SmartUI Fusion! Deployed via EC2 tunnel! 🎉');
    });
    
    let deployStatus = vscode.commands.registerCommand('smartui-fusion.deployStatus', () => {
        const now = new Date().toLocaleString();
        vscode.window.showInformationMessage(`SmartUI Fusion deployed successfully at ${now} ✅`);
    });
    
    context.subscriptions.push(helloWorld, deployStatus);
    
    // 顯示激活通知
    vscode.window.showInformationMessage('SmartUI Fusion extension loaded! 🚀');
}

export function deactivate() {}
EXTENSION_EOF
        
        log_success "VS Code 擴展項目已創建"
    fi
    
    # 複製到構建目錄
    cp -r "$PROJECT_DIR/vscode-extension" "$LOCAL_BUILD_DIR/"
    log_success "構建環境準備完成"
}

# 構建 VSIX
build_vsix() {
    log_info "構建 VSIX 擴展..."
    
    cd "$LOCAL_BUILD_DIR/vscode-extension"
    
    # 安裝依賴
    log_info "安裝依賴..."
    npm install
    
    # 編譯
    if [[ -f "tsconfig.json" ]]; then
        log_info "編譯 TypeScript..."
        npm run compile 2>/dev/null || npx tsc || log_warning "編譯警告，繼續打包..."
    fi
    
    # 安裝 vsce
    if ! command -v vsce &> /dev/null; then
        log_info "安裝 vsce..."
        npm install -g vsce
    fi
    
    # 打包
    log_info "打包 VSIX..."
    vsce package --out "$LOCAL_BUILD_DIR/"
    
    VSIX_FILE=$(find "$LOCAL_BUILD_DIR" -name "*.vsix" -type f | head -1)
    if [[ -n "$VSIX_FILE" ]]; then
        log_success "VSIX 構建完成: $(basename "$VSIX_FILE")"
        echo "$VSIX_FILE"
    else
        log_error "VSIX 構建失敗"
        return 1
    fi
}

# 部署到 Mac
deploy_to_mac() {
    local vsix_path="$1"
    local filename=$(basename "$vsix_path")
    
    log_info "部署 VSIX 到 Mac..."
    
    # 確保目錄存在
    ssh -p $MAC_PORT $MAC_USER@$MAC_HOST "mkdir -p $MAC_DEPLOY_DIR/incoming"
    
    # 傳輸文件
    log_info "傳輸 $filename 到 Mac..."
    scp -P $MAC_PORT "$vsix_path" "$MAC_USER@$MAC_HOST:$MAC_DEPLOY_DIR/incoming/"
    
    # 觸發安裝
    log_info "觸發 Mac 端安裝..."
    ssh -p $MAC_PORT $MAC_USER@$MAC_HOST "$MAC_DEPLOY_DIR/remote_deploy_handler.sh"
    
    log_success "🎉 部署完成！請在 VS Code 中重新加載窗口"
}

# 主函數
main() {
    log_info "🚀 SmartUI Fusion 完整部署開始..."
    
    if ! check_connection; then
        exit 1
    fi
    
    prepare_build
    
    VSIX_FILE=$(build_vsix)
    if [[ -z "$VSIX_FILE" ]]; then
        exit 1
    fi
    
    deploy_to_mac "$VSIX_FILE"
    
    # 清理
    rm -rf "$LOCAL_BUILD_DIR"
    
    log_success "🎉 SmartUI Fusion 部署完成！"
}

main "$@"

