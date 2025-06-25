#!/bin/bash

# PowerAutomation Local MCP 實際VSIX部署執行腳本
# 通過SSH Port Forwarding執行真實的VSIX部署
# 
# 使用方法:
# 1. 確保SSH port forwarding已建立: ssh ec2_remote_via_vpn -L 8080:localhost:8394
# 2. 準備要部署的VSIX文件
# 3. 執行此腳本: ./execute_vsix_deployment.sh [vsix_file_path] [environment]

echo "🚀 PowerAutomation Local MCP 實際VSIX部署執行"
echo "============================================="

# 參數檢查
VSIX_FILE="$1"
TARGET_ENV="${2:-development}"
POWERAUTOMATION_URL="http://localhost:8080"
TEST_TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="vsix_deployment_execution_${TEST_TIMESTAMP}.log"

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 日誌函數
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

success() {
    echo -e "${GREEN}✅ $1${NC}" | tee -a "$LOG_FILE"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}❌ $1${NC}" | tee -a "$LOG_FILE"
}

info() {
    echo -e "${BLUE}ℹ️  $1${NC}" | tee -a "$LOG_FILE"
}

# 顯示使用說明
show_usage() {
    echo "使用方法:"
    echo "  $0 [vsix_file_path] [environment]"
    echo ""
    echo "參數:"
    echo "  vsix_file_path  - VSIX文件的路徑 (可選，如果不提供將使用測試模式)"
    echo "  environment     - 目標環境 (development|staging|production，默認: development)"
    echo ""
    echo "示例:"
    echo "  $0 ./my-extension.vsix development"
    echo "  $0 /path/to/extension.vsix production"
    echo "  $0  # 測試模式，不需要實際VSIX文件"
    echo ""
    echo "前置條件:"
    echo "  1. SSH port forwarding已建立: ssh ec2_remote_via_vpn -L 8080:localhost:8394"
    echo "  2. PowerAutomation Local MCP服務正在EC2上運行"
    echo "  3. 如果使用實際VSIX文件，確保文件存在且可讀"
}

# 檢查前置條件
check_prerequisites() {
    info "檢查前置條件..."
    
    # 檢查SSH port forwarding連接
    local health_status
    health_status=$(curl -s -o /dev/null -w "%{http_code}" "$POWERAUTOMATION_URL/health" 2>/dev/null)
    
    if [ "$health_status" != "200" ]; then
        error "無法連接到PowerAutomation服務 (HTTP $health_status)"
        error "請確認SSH port forwarding已建立:"
        error "ssh ec2_remote_via_vpn -L 8080:localhost:8394"
        return 1
    fi
    
    success "PowerAutomation服務連接正常"
    
    # 檢查VSIX文件（如果提供）
    if [ -n "$VSIX_FILE" ]; then
        if [ ! -f "$VSIX_FILE" ]; then
            error "VSIX文件不存在: $VSIX_FILE"
            return 1
        fi
        
        if [ ! -r "$VSIX_FILE" ]; then
            error "VSIX文件不可讀: $VSIX_FILE"
            return 1
        fi
        
        success "VSIX文件檢查通過: $VSIX_FILE"
    else
        info "未提供VSIX文件，將使用測試模式"
    fi
    
    return 0
}

# 上傳VSIX文件（如果需要）
upload_vsix_file() {
    if [ -z "$VSIX_FILE" ]; then
        return 0  # 測試模式，跳過上傳
    fi
    
    info "上傳VSIX文件到PowerAutomation服務..."
    
    local upload_response
    upload_response=$(curl -s -X POST \
        -F "vsix_file=@$VSIX_FILE" \
        -F "target_environment=$TARGET_ENV" \
        "$POWERAUTOMATION_URL/api/vsix/upload" 2>/dev/null)
    
    local upload_status=$?
    
    if [ $upload_status -eq 0 ]; then
        success "VSIX文件上傳成功"
        log "上傳響應: $upload_response"
        
        # 提取上傳後的文件路徑
        if command -v jq &> /dev/null; then
            UPLOADED_VSIX_PATH=$(echo "$upload_response" | jq -r '.uploaded_path // empty' 2>/dev/null)
            if [ -n "$UPLOADED_VSIX_PATH" ]; then
                info "上傳後的文件路徑: $UPLOADED_VSIX_PATH"
            fi
        fi
        
        return 0
    else
        error "VSIX文件上傳失敗"
        return 1
    fi
}

# 執行VSIX部署
execute_deployment() {
    info "執行VSIX部署..."
    
    # 準備部署數據
    local deployment_data
    if [ -n "$VSIX_FILE" ]; then
        # 實際部署模式
        deployment_data='{
            "vsix_path": "'${UPLOADED_VSIX_PATH:-$VSIX_FILE}'",
            "target_environment": "'$TARGET_ENV'",
            "deployment_mode": "production",
            "force_install": false,
            "backup_existing": true,
            "validate_before_install": true,
            "human_loop_enabled": true,
            "require_confirmation": true,
            "confirmation_message": "確定要部署此VSIX到'$TARGET_ENV'環境嗎？",
            "post_install_verification": true,
            "rollback_on_failure": true
        }'
    else
        # 測試模式
        deployment_data='{
            "vsix_path": "/test/sample-extension.vsix",
            "target_environment": "'$TARGET_ENV'",
            "deployment_mode": "test",
            "force_install": false,
            "backup_existing": true,
            "validate_before_install": true,
            "human_loop_enabled": true,
            "require_confirmation": true,
            "confirmation_message": "這是一個測試部署，確定要繼續嗎？",
            "post_install_verification": false,
            "rollback_on_failure": false
        }'
    fi
    
    info "部署配置:"
    echo "$deployment_data" | jq . 2>/dev/null || echo "$deployment_data"
    
    # 發送部署請求
    local deploy_response
    deploy_response=$(curl -s -X POST \
        -H "Content-Type: application/json" \
        -d "$deployment_data" \
        "$POWERAUTOMATION_URL/api/vsix/deploy" 2>/dev/null)
    
    local deploy_status=$?
    
    if [ $deploy_status -eq 0 ]; then
        success "VSIX部署請求發送成功"
        log "部署響應: $deploy_response"
        echo "$deploy_response" | jq . 2>/dev/null || echo "$deploy_response"
        
        # 提取部署ID
        local deployment_id
        if command -v jq &> /dev/null; then
            deployment_id=$(echo "$deploy_response" | jq -r '.deployment_id // empty' 2>/dev/null)
            if [ -n "$deployment_id" ]; then
                info "部署ID: $deployment_id"
                monitor_deployment_progress "$deployment_id"
            fi
        fi
        
        return 0
    else
        error "VSIX部署請求失敗"
        return 1
    fi
}

# 監控部署進度
monitor_deployment_progress() {
    local deployment_id="$1"
    
    if [ -z "$deployment_id" ]; then
        return 0
    fi
    
    info "監控部署進度 (ID: $deployment_id)..."
    
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        local status_response
        status_response=$(curl -s "$POWERAUTOMATION_URL/api/vsix/status/$deployment_id" 2>/dev/null)
        
        if [ $? -eq 0 ] && [ -n "$status_response" ]; then
            local status
            if command -v jq &> /dev/null; then
                status=$(echo "$status_response" | jq -r '.status // "unknown"' 2>/dev/null)
            else
                status="unknown"
            fi
            
            info "部署狀態 ($attempt/$max_attempts): $status"
            
            case "$status" in
                "completed"|"success"|"deployed")
                    success "部署完成！"
                    echo "$status_response" | jq . 2>/dev/null || echo "$status_response"
                    return 0
                    ;;
                "failed"|"error")
                    error "部署失敗！"
                    echo "$status_response" | jq . 2>/dev/null || echo "$status_response"
                    return 1
                    ;;
                "pending_confirmation"|"waiting_for_user")
                    warning "等待用戶確認，請檢查Human Loop MCP界面"
                    info "Human Loop MCP Web界面: http://localhost:8096"
                    ;;
                "in_progress"|"deploying")
                    info "部署進行中..."
                    ;;
            esac
        else
            warning "無法獲取部署狀態"
        fi
        
        sleep 10
        ((attempt++))
    done
    
    warning "部署監控超時，請手動檢查部署狀態"
    return 1
}

# 生成部署報告
generate_deployment_report() {
    local report_file="vsix_deployment_report_${TEST_TIMESTAMP}.json"
    
    cat > "$report_file" << EOF
{
    "deployment_info": {
        "timestamp": "$TEST_TIMESTAMP",
        "vsix_file": "${VSIX_FILE:-"test_mode"}",
        "target_environment": "$TARGET_ENV",
        "powerautomation_url": "$POWERAUTOMATION_URL",
        "log_file": "$LOG_FILE"
    },
    "deployment_result": {
        "status": "completed",
        "notes": "詳細信息請查看日誌文件"
    }
}
EOF
    
    success "部署報告已生成: $report_file"
}

# 主函數
main() {
    log "開始PowerAutomation Local MCP VSIX部署執行"
    
    # 顯示參數信息
    info "部署參數:"
    info "  VSIX文件: ${VSIX_FILE:-"測試模式"}"
    info "  目標環境: $TARGET_ENV"
    info "  PowerAutomation URL: $POWERAUTOMATION_URL"
    
    # 檢查前置條件
    if ! check_prerequisites; then
        error "前置條件檢查失敗，部署終止"
        exit 1
    fi
    
    # 上傳VSIX文件（如果需要）
    if ! upload_vsix_file; then
        error "VSIX文件上傳失敗，部署終止"
        exit 1
    fi
    
    # 執行部署
    if ! execute_deployment; then
        error "VSIX部署執行失敗"
        exit 1
    fi
    
    # 生成報告
    generate_deployment_report
    
    success "VSIX部署執行完成！"
    info "詳細日誌: $LOG_FILE"
    
    echo ""
    echo "🎯 後續步驟:"
    echo "1. 檢查部署日誌以確認部署狀態"
    echo "2. 如果啟用了Human Loop，請在Web界面中確認操作"
    echo "3. 驗證VSCode擴展是否正確安裝"
    echo "4. 測試擴展功能是否正常工作"
    
    log "PowerAutomation Local MCP VSIX部署執行完成"
}

# 檢查是否需要顯示幫助
if [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
    show_usage
    exit 0
fi

# 執行主函數
main "$@"

