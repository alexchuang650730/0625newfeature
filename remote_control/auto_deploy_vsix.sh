#!/bin/bash

# EC2 端自動化 VSIX 部署腳本
# 用於從 EC2 自動構建、打包和部署 VSIX 到 Mac

set -e  # 遇到錯誤立即退出

# 配置變量
MAC_HOST="ec2_remote_via_vpn"
MAC_USER="alexchuang"  # 請根據實際情況修改
MAC_DEPLOY_DIR="/Users/$MAC_USER/vsix_deploy"
LOCAL_BUILD_DIR="/tmp/vsix_build"
PROJECT_DIR="/home/ubuntu/0625newfeature"

# 顏色輸出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 檢查依賴
check_dependencies() {
    log_info "檢查依賴項..."
    
    # 檢查 SSH 連接
    if ! ssh -o ConnectTimeout=5 "$MAC_HOST" "echo 'SSH connection test'" > /dev/null 2>&1; then
        log_error "無法連接到 Mac ($MAC_HOST)"
        log_info "請確保:"
        log_info "1. VPN 連接正常"
        log_info "2. SSH 配置正確"
        log_info "3. Mac 端 SSH 服務已啟用"
        exit 1
    fi
    log_success "SSH 連接正常"
    
    # 檢查 Node.js
    if ! command -v npm &> /dev/null; then
        log_error "npm 未安裝，正在安裝..."
        curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
        sudo apt-get install -y nodejs
    fi
    log_success "Node.js 環境正常"
    
    # 檢查 vsce (VS Code Extension Manager)
    if ! command -v vsce &> /dev/null; then
        log_info "安裝 vsce..."
        npm install -g vsce
    fi
    log_success "vsce 工具已安裝"
}

# 準備構建環境
prepare_build_env() {
    log_info "準備構建環境..."
    
    # 清理並創建構建目錄
    rm -rf "$LOCAL_BUILD_DIR"
    mkdir -p "$LOCAL_BUILD_DIR"
    
    # 複製 VS Code 擴展項目
    if [ -d "$PROJECT_DIR/vscode-extension" ]; then
        cp -r "$PROJECT_DIR/vscode-extension" "$LOCAL_BUILD_DIR/"
        log_success "VS Code 擴展項目已複製"
    else
        log_error "VS Code 擴展項目不存在: $PROJECT_DIR/vscode-extension"
        exit 1
    fi
}

# 構建 VSIX
build_vsix() {
    log_info "構建 VSIX 擴展..."
    
    cd "$LOCAL_BUILD_DIR/vscode-extension"
    
    # 安裝依賴
    log_info "安裝 npm 依賴..."
    npm install
    
    # 編譯 TypeScript
    if [ -f "tsconfig.json" ]; then
        log_info "編譯 TypeScript..."
        npm run compile 2>/dev/null || npx tsc
    fi
    
    # 打包 VSIX
    log_info "打包 VSIX..."
    VSIX_FILE=$(vsce package --out "$LOCAL_BUILD_DIR/" 2>&1 | grep -o '[^/]*\.vsix$' | tail -1)
    
    if [ -z "$VSIX_FILE" ]; then
        log_error "VSIX 打包失敗"
        exit 1
    fi
    
    VSIX_PATH="$LOCAL_BUILD_DIR/$VSIX_FILE"
    if [ ! -f "$VSIX_PATH" ]; then
        log_error "VSIX 文件未生成: $VSIX_PATH"
        exit 1
    fi
    
    log_success "VSIX 構建完成: $VSIX_FILE"
    echo "$VSIX_PATH"
}

# 部署到 Mac
deploy_to_mac() {
    local vsix_path="$1"
    local vsix_filename=$(basename "$vsix_path")
    
    log_info "部署 VSIX 到 Mac..."
    
    # 確保 Mac 端部署目錄存在
    ssh "$MAC_HOST" "mkdir -p $MAC_DEPLOY_DIR/incoming"
    
    # 傳輸 VSIX 文件
    log_info "傳輸 VSIX 文件..."
    if scp "$vsix_path" "$MAC_HOST:$MAC_DEPLOY_DIR/incoming/"; then
        log_success "VSIX 文件傳輸完成"
    else
        log_error "VSIX 文件傳輸失敗"
        exit 1
    fi
    
    # 觸發 Mac 端安裝
    log_info "觸發 Mac 端安裝..."
    ssh "$MAC_HOST" "$MAC_DEPLOY_DIR/remote_deploy_handler.sh"
    
    # 檢查安裝結果
    log_info "檢查安裝結果..."
    if ssh "$MAC_HOST" "ls $MAC_DEPLOY_DIR/processed_*$vsix_filename 2>/dev/null"; then
        log_success "VSIX 安裝成功!"
    elif ssh "$MAC_HOST" "ls $MAC_DEPLOY_DIR/failed/*$vsix_filename 2>/dev/null"; then
        log_error "VSIX 安裝失敗!"
        exit 1
    else
        log_warning "安裝狀態未知，請手動檢查"
    fi
}

# 獲取部署狀態
get_deployment_status() {
    log_info "獲取 Mac 端部署狀態..."
    ssh "$MAC_HOST" "$MAC_DEPLOY_DIR/check_status.sh"
}

# 清理構建文件
cleanup() {
    log_info "清理構建文件..."
    rm -rf "$LOCAL_BUILD_DIR"
    log_success "清理完成"
}

# 主函數
main() {
    log_info "🚀 開始自動化 VSIX 部署流程..."
    
    # 解析命令行參數
    SKIP_BUILD=false
    VSIX_FILE=""
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-build)
                SKIP_BUILD=true
                shift
                ;;
            --vsix-file)
                VSIX_FILE="$2"
                SKIP_BUILD=true
                shift 2
                ;;
            --status)
                get_deployment_status
                exit 0
                ;;
            --help)
                echo "用法: $0 [選項]"
                echo "選項:"
                echo "  --skip-build     跳過構建，直接部署現有 VSIX"
                echo "  --vsix-file FILE 指定要部署的 VSIX 文件"
                echo "  --status         檢查 Mac 端部署狀態"
                echo "  --help           顯示此幫助信息"
                exit 0
                ;;
            *)
                log_error "未知選項: $1"
                exit 1
                ;;
        esac
    done
    
    # 檢查依賴
    check_dependencies
    
    if [ "$SKIP_BUILD" = false ]; then
        # 準備構建環境
        prepare_build_env
        
        # 構建 VSIX
        VSIX_FILE=$(build_vsix)
    else
        if [ -z "$VSIX_FILE" ]; then
            log_error "請指定 VSIX 文件路徑 (--vsix-file)"
            exit 1
        fi
        
        if [ ! -f "$VSIX_FILE" ]; then
            log_error "VSIX 文件不存在: $VSIX_FILE"
            exit 1
        fi
    fi
    
    # 部署到 Mac
    deploy_to_mac "$VSIX_FILE"
    
    # 獲取部署狀態
    get_deployment_status
    
    # 清理
    if [ "$SKIP_BUILD" = false ]; then
        cleanup
    fi
    
    log_success "🎉 自動化部署完成!"
    log_info "💡 提示: 建議重啟 VS Code 以加載新擴展"
}

# 錯誤處理
trap 'log_error "腳本執行失敗，正在清理..."; cleanup; exit 1' ERR

# 執行主函數
main "$@"

