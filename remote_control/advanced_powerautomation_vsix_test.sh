#!/bin/bash

# PowerAutomation Local MCP 高級VSIX部署測試腳本
# 包含Human Loop MCP集成測試
# 
# 使用方法:
# 1. 確保SSH port forwarding已建立: ssh ec2_remote_via_vpn -L 8080:localhost:8394
# 2. 在Mac終端中執行此腳本: ./advanced_powerautomation_vsix_test.sh

echo "🚀 PowerAutomation Local MCP 高級VSIX部署測試"
echo "=============================================="

# 設置變量
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="$SCRIPT_DIR/powerautomation_vsix_test_config.json"
LOCAL_PORT=8080
POWERAUTOMATION_URL="http://localhost:${LOCAL_PORT}"
TEST_TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="advanced_powerautomation_test_${TEST_TIMESTAMP}.log"
REPORT_FILE="advanced_powerautomation_report_${TEST_TIMESTAMP}.json"

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 創建日誌函數
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

# 檢查依賴
check_dependencies() {
    info "檢查依賴工具..."
    
    if ! command -v curl &> /dev/null; then
        error "curl 未安裝，請安裝後重試"
        exit 1
    fi
    
    if ! command -v jq &> /dev/null; then
        warning "jq 未安裝，JSON格式化將不可用"
        JQ_AVAILABLE=false
    else
        JQ_AVAILABLE=true
    fi
    
    success "依賴檢查完成"
}

# 格式化JSON輸出
format_json() {
    if [ "$JQ_AVAILABLE" = true ]; then
        echo "$1" | jq . 2>/dev/null || echo "$1"
    else
        echo "$1"
    fi
}

# HTTP請求函數
make_request() {
    local method="$1"
    local endpoint="$2"
    local data="$3"
    local description="$4"
    
    info "發送 $method 請求到 $endpoint"
    if [ -n "$description" ]; then
        info "描述: $description"
    fi
    
    local url="$POWERAUTOMATION_URL$endpoint"
    local response
    local http_code
    
    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" "$url" 2>/dev/null)
    elif [ "$method" = "POST" ]; then
        response=$(curl -s -w "\n%{http_code}" -X POST \
            -H "Content-Type: application/json" \
            -d "$data" \
            "$url" 2>/dev/null)
    fi
    
    http_code=$(echo "$response" | tail -n1)
    response_body=$(echo "$response" | head -n -1)
    
    log "HTTP狀態碼: $http_code"
    log "響應內容: $response_body"
    
    echo "$response_body"
    return $http_code
}

# 初始化測試報告
init_report() {
    cat > "$REPORT_FILE" << EOF
{
    "test_info": {
        "timestamp": "$TEST_TIMESTAMP",
        "script_version": "2.0",
        "test_type": "advanced_powerautomation_vsix_deployment",
        "configuration": {
            "local_port": $LOCAL_PORT,
            "powerautomation_url": "$POWERAUTOMATION_URL",
            "config_file": "$CONFIG_FILE"
        }
    },
    "test_results": {}
}
EOF
}

# 更新測試報告
update_report() {
    local test_name="$1"
    local result="$2"
    local status="$3"
    
    # 使用臨時文件更新JSON
    if [ "$JQ_AVAILABLE" = true ]; then
        jq ".test_results[\"$test_name\"] = {\"result\": $result, \"status\": \"$status\", \"timestamp\": \"$(date -Iseconds)\"}" "$REPORT_FILE" > "${REPORT_FILE}.tmp" && mv "${REPORT_FILE}.tmp" "$REPORT_FILE"
    fi
}

# 測試1: 基本連接測試
test_basic_connectivity() {
    echo ""
    info "🔗 測試1: 基本連接測試"
    echo "========================"
    
    # 測試健康檢查
    local health_response
    health_response=$(make_request "GET" "/health" "" "PowerAutomation健康檢查")
    local health_status=$?
    
    if [ $health_status -eq 200 ]; then
        success "PowerAutomation健康檢查成功"
        format_json "$health_response"
        update_report "basic_connectivity" "$(echo "$health_response" | jq -c . 2>/dev/null || echo "\"$health_response\"")" "success"
    else
        error "PowerAutomation健康檢查失敗 (HTTP $health_status)"
        update_report "basic_connectivity" "\"HTTP $health_status\"" "failed"
        return 1
    fi
    
    # 測試組件狀態
    local components_response
    components_response=$(make_request "GET" "/api/components" "" "組件狀態檢查")
    local components_status=$?
    
    if [ $components_status -eq 200 ]; then
        success "組件狀態檢查成功"
        format_json "$components_response"
    else
        warning "組件狀態檢查失敗 (HTTP $components_status)"
    fi
    
    return 0
}

# 測試2: Enhanced VSCode Installer MCP測試
test_enhanced_vscode_installer_mcp() {
    echo ""
    info "🔌 測試2: Enhanced VSCode Installer MCP測試"
    echo "==========================================="
    
    local mcp_endpoint="/api/mcp/enhanced_vscode_installer"
    local mcp_response
    mcp_response=$(make_request "GET" "$mcp_endpoint" "" "Enhanced VSCode Installer MCP狀態檢查")
    local mcp_status=$?
    
    if [ $mcp_status -eq 200 ]; then
        success "Enhanced VSCode Installer MCP可訪問"
        format_json "$mcp_response"
        update_report "enhanced_vscode_installer_mcp" "$(echo "$mcp_response" | jq -c . 2>/dev/null || echo "\"$mcp_response\"")" "success"
    else
        error "Enhanced VSCode Installer MCP不可訪問 (HTTP $mcp_status)"
        update_report "enhanced_vscode_installer_mcp" "\"HTTP $mcp_status\"" "failed"
        return 1
    fi
    
    return 0
}

# 測試3: VSIX部署功能測試
test_vsix_deployment() {
    echo ""
    info "🚀 測試3: VSIX部署功能測試"
    echo "=========================="
    
    local test_data='{
        "vsix_path": "/test/sample-extension.vsix",
        "target_environment": "development",
        "deployment_mode": "test",
        "force_install": false,
        "backup_existing": true,
        "validate_before_install": true,
        "human_loop_enabled": true
    }'
    
    local deploy_response
    deploy_response=$(make_request "POST" "/api/vsix/deploy" "$test_data" "VSIX部署測試")
    local deploy_status=$?
    
    if [ $deploy_status -eq 200 ] || [ $deploy_status -eq 202 ]; then
        success "VSIX部署請求成功 (HTTP $deploy_status)"
        format_json "$deploy_response"
        update_report "vsix_deployment" "$(echo "$deploy_response" | jq -c . 2>/dev/null || echo "\"$deploy_response\"")" "success"
        
        # 如果返回了部署ID，檢查部署狀態
        local deployment_id
        if [ "$JQ_AVAILABLE" = true ]; then
            deployment_id=$(echo "$deploy_response" | jq -r '.deployment_id // empty' 2>/dev/null)
            if [ -n "$deployment_id" ]; then
                info "檢查部署狀態 (ID: $deployment_id)"
                local status_response
                status_response=$(make_request "GET" "/api/vsix/status/$deployment_id" "" "部署狀態檢查")
                format_json "$status_response"
            fi
        fi
    else
        error "VSIX部署請求失敗 (HTTP $deploy_status)"
        update_report "vsix_deployment" "\"HTTP $deploy_status\"" "failed"
        return 1
    fi
    
    return 0
}

# 測試4: Human Loop MCP集成測試
test_human_loop_integration() {
    echo ""
    info "🤝 測試4: Human Loop MCP集成測試"
    echo "==============================="
    
    # 檢查Human Loop MCP服務
    local human_loop_response
    human_loop_response=$(make_request "GET" "/api/human_loop/health" "" "Human Loop MCP健康檢查")
    local human_loop_status=$?
    
    if [ $human_loop_status -eq 200 ]; then
        success "Human Loop MCP服務可訪問"
        format_json "$human_loop_response"
    else
        warning "Human Loop MCP服務不可訪問 (HTTP $human_loop_status)"
        info "這可能是正常的，如果Human Loop MCP未啟用"
    fi
    
    # 測試創建交互會話
    local interaction_data='{
        "interaction_data": {
            "interaction_type": "confirmation",
            "title": "VSIX部署確認測試",
            "message": "這是一個測試確認對話框，用於驗證Human Loop MCP集成功能。",
            "options": [
                {"value": "confirm", "label": "確認"},
                {"value": "cancel", "label": "取消"}
            ],
            "timeout": 300
        },
        "workflow_id": "vsix_deployment_test_'$TEST_TIMESTAMP'",
        "callback_url": null
    }'
    
    local session_response
    session_response=$(make_request "POST" "/api/human_loop/sessions" "$interaction_data" "創建Human Loop交互會話")
    local session_status=$?
    
    if [ $session_status -eq 200 ] || [ $session_status -eq 201 ]; then
        success "Human Loop交互會話創建成功"
        format_json "$session_response"
        update_report "human_loop_integration" "$(echo "$session_response" | jq -c . 2>/dev/null || echo "\"$session_response\"")" "success"
        
        # 提取會話ID
        local session_id
        if [ "$JQ_AVAILABLE" = true ]; then
            session_id=$(echo "$session_response" | jq -r '.session_id // empty' 2>/dev/null)
            if [ -n "$session_id" ]; then
                info "交互會話已創建，會話ID: $session_id"
                info "您可以在Human Loop MCP Web界面中查看此會話"
                info "Web界面地址: http://localhost:8096 (如果Human Loop MCP在默認端口運行)"
            fi
        fi
    else
        warning "Human Loop交互會話創建失敗 (HTTP $session_status)"
        update_report "human_loop_integration" "\"HTTP $session_status\"" "failed"
    fi
    
    return 0
}

# 測試5: 綜合集成測試
test_comprehensive_integration() {
    echo ""
    info "🎯 測試5: 綜合集成測試"
    echo "======================"
    
    info "執行完整的VSIX部署流程，包含Human Loop確認"
    
    # 步驟1: 預檢查
    local precheck_data='{
        "vsix_path": "/test/comprehensive-test.vsix",
        "target_environment": "development",
        "check_only": true
    }'
    
    local precheck_response
    precheck_response=$(make_request "POST" "/api/vsix/precheck" "$precheck_data" "VSIX部署預檢查")
    local precheck_status=$?
    
    if [ $precheck_status -eq 200 ]; then
        success "VSIX部署預檢查成功"
        format_json "$precheck_response"
    else
        warning "VSIX部署預檢查失敗或不支持 (HTTP $precheck_status)"
    fi
    
    # 步驟2: 帶Human Loop確認的部署
    local comprehensive_data='{
        "vsix_path": "/test/comprehensive-test.vsix",
        "target_environment": "development",
        "deployment_mode": "interactive",
        "human_loop_enabled": true,
        "require_confirmation": true,
        "confirmation_message": "綜合測試：確定要部署此VSIX嗎？",
        "backup_existing": true,
        "validate_before_install": true,
        "post_install_verification": true
    }'
    
    local comprehensive_response
    comprehensive_response=$(make_request "POST" "/api/vsix/deploy" "$comprehensive_data" "綜合VSIX部署測試")
    local comprehensive_status=$?
    
    if [ $comprehensive_status -eq 200 ] || [ $comprehensive_status -eq 202 ]; then
        success "綜合VSIX部署測試成功"
        format_json "$comprehensive_response"
        update_report "comprehensive_integration" "$(echo "$comprehensive_response" | jq -c . 2>/dev/null || echo "\"$comprehensive_response\"")" "success"
    else
        error "綜合VSIX部署測試失敗 (HTTP $comprehensive_status)"
        update_report "comprehensive_integration" "\"HTTP $comprehensive_status\"" "failed"
    fi
    
    return 0
}

# 生成最終報告
generate_final_report() {
    echo ""
    info "📊 生成最終測試報告"
    echo "==================="
    
    # 添加總結信息到報告
    if [ "$JQ_AVAILABLE" = true ]; then
        jq ".summary = {
            \"total_tests\": 5,
            \"log_file\": \"$LOG_FILE\",
            \"report_file\": \"$REPORT_FILE\",
            \"test_duration\": \"$(date -Iseconds)\",
            \"recommendations\": [
                \"確保SSH port forwarding連接穩定\",
                \"檢查PowerAutomation Local MCP服務狀態\",
                \"驗證Human Loop MCP集成配置\",
                \"測試實際VSIX文件部署\"
            ]
        }" "$REPORT_FILE" > "${REPORT_FILE}.tmp" && mv "${REPORT_FILE}.tmp" "$REPORT_FILE"
    fi
    
    success "測試報告已生成: $REPORT_FILE"
    success "詳細日誌已保存: $LOG_FILE"
}

# 主函數
main() {
    log "開始PowerAutomation Local MCP高級VSIX部署測試"
    
    # 初始化
    check_dependencies
    init_report
    
    # 執行測試
    local test_results=0
    
    test_basic_connectivity || ((test_results++))
    test_enhanced_vscode_installer_mcp || ((test_results++))
    test_vsix_deployment || ((test_results++))
    test_human_loop_integration || ((test_results++))
    test_comprehensive_integration || ((test_results++))
    
    # 生成報告
    generate_final_report
    
    # 顯示總結
    echo ""
    echo "🎯 測試總結"
    echo "============"
    if [ $test_results -eq 0 ]; then
        success "所有測試完成！"
    else
        warning "$test_results 個測試遇到問題，請查看詳細日誌"
    fi
    
    echo ""
    echo "📄 查看測試報告:"
    echo "cat $REPORT_FILE | jq ."
    echo ""
    echo "📝 查看詳細日誌:"
    echo "cat $LOG_FILE"
    echo ""
    echo "🌐 如果Human Loop MCP已啟用，請訪問:"
    echo "http://localhost:8096"
    
    log "PowerAutomation Local MCP高級VSIX部署測試完成"
}

# 執行主函數
main "$@"

