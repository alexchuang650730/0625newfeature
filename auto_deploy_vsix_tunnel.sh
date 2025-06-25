#!/bin/bash

# 適配反向隧道的 VSIX 自動部署腳本
set -e

# 配置變量
MAC_HOST="localhost"
MAC_PORT="2222"
MAC_USER="alexchuang"  # Mac 端用戶名

# 顏色輸出
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 檢查反向隧道連接
check_tunnel_connection() {
    log_info "檢查反向隧道連接..."
    
    if netstat -tlnp 2>/dev/null | grep ":$MAC_PORT" > /dev/null; then
        log_success "反向隧道端口 $MAC_PORT 正在監聽"
    else
        log_error "反向隧道端口 $MAC_PORT 未監聽"
        return 1
    fi
    
    log_info "測試 SSH 連接到 Mac (需要輸入 Mac 用戶密碼)..."
    if ssh -p $MAC_PORT -o ConnectTimeout=10 $MAC_USER@$MAC_HOST "echo 'SSH connection test successful'"; then
        log_success "SSH 連接到 Mac 成功"
        return 0
    else
        log_error "SSH 連接到 Mac 失敗"
        return 1
    fi
}

# 傳輸文件到 Mac
transfer_file() {
    local file_path="$1"
    local filename=$(basename "$file_path")
    
    log_info "傳輸文件到 Mac: $filename"
    if scp -P $MAC_PORT "$file_path" "$MAC_USER@$MAC_HOST:/Users/$MAC_USER/vsix_deploy/incoming/"; then
        log_success "文件傳輸成功"
        return 0
    else
        log_error "文件傳輸失敗"
        return 1
    fi
}

# 主函數
main() {
    case "${1:-test}" in
        "test")
            log_info "🚀 SmartUI Fusion 反向隧道測試..."
            if check_tunnel_connection; then
                log_success "🎉 隧道連接測試成功！"
            else
                log_error "❌ 隧道連接失敗"
                exit 1
            fi
            ;;
        "deploy")
            log_info "🚀 開始部署流程..."
            if check_tunnel_connection; then
                log_info "連接正常，準備部署..."
                # 這裡後續添加構建和部署邏輯
                log_success "🎉 部署準備完成！"
            else
                log_error "❌ 連接失敗，無法部署"
                exit 1
            fi
            ;;
        *)
            echo "用法: $0 [test|deploy]"
            echo "  test   - 測試隧道連接"
            echo "  deploy - 執行完整部署"
            ;;
    esac
}

main "$@"

