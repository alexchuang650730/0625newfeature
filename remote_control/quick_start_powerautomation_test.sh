#!/bin/bash

# PowerAutomation VSIX部署測試 - 快速開始腳本
# 自動設置測試環境並執行基本測試

echo "🚀 PowerAutomation VSIX部署測試 - 快速開始"
echo "=========================================="

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# 檢查SSH port forwarding連接
check_connection() {
    info "檢查SSH port forwarding連接..."
    
    local status
    status=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/health 2>/dev/null)
    
    if [ "$status" = "200" ]; then
        success "SSH port forwarding連接正常"
        return 0
    else
        error "SSH port forwarding連接失敗 (HTTP $status)"
        echo ""
        echo "請確保已建立SSH連接："
        echo "ssh ec2_remote_via_vpn -L 8080:localhost:8394"
        echo ""
        return 1
    fi
}

# 檢查必要工具
check_tools() {
    info "檢查必要工具..."
    
    if ! command -v curl &> /dev/null; then
        error "curl 未安裝"
        return 1
    fi
    
    if ! command -v jq &> /dev/null; then
        warning "jq 未安裝，建議安裝以獲得更好的JSON格式化"
        echo "安裝命令: brew install jq"
    else
        success "jq 已安裝"
    fi
    
    success "工具檢查完成"
    return 0
}

# 執行快速測試
run_quick_test() {
    info "執行快速連接測試..."
    
    echo ""
    echo "📡 測試PowerAutomation健康狀態"
    local health_response
    health_response=$(curl -s http://localhost:8080/health 2>/dev/null)
    
    if [ $? -eq 0 ] && [ -n "$health_response" ]; then
        success "PowerAutomation健康檢查成功"
        echo "$health_response" | jq . 2>/dev/null || echo "$health_response"
    else
        error "PowerAutomation健康檢查失敗"
        return 1
    fi
    
    echo ""
    echo "🔌 測試Enhanced VSCode Installer MCP"
    local mcp_status
    mcp_status=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/api/mcp/enhanced_vscode_installer 2>/dev/null)
    
    if [ "$mcp_status" = "200" ]; then
        success "Enhanced VSCode Installer MCP可訪問"
    else
        warning "Enhanced VSCode Installer MCP狀態: HTTP $mcp_status"
    fi
    
    echo ""
    echo "🚀 測試VSIX部署端點"
    local vsix_status
    vsix_status=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/api/vsix/deploy 2>/dev/null)
    
    if [ "$vsix_status" = "200" ] || [ "$vsix_status" = "405" ]; then
        success "VSIX部署端點可訪問"
    else
        warning "VSIX部署端點狀態: HTTP $vsix_status"
    fi
    
    return 0
}

# 顯示下一步指引
show_next_steps() {
    echo ""
    echo "🎯 快速測試完成！下一步操作："
    echo "================================"
    echo ""
    echo "1. 執行完整的基礎測試："
    echo "   ./test_powerautomation_vsix_deployment.sh"
    echo ""
    echo "2. 執行高級集成測試："
    echo "   ./advanced_powerautomation_vsix_test.sh"
    echo ""
    echo "3. 執行實際VSIX部署："
    echo "   ./execute_vsix_deployment.sh [vsix_file] [environment]"
    echo ""
    echo "4. 查看完整使用指南："
    echo "   cat PowerAutomation_VSIX_Deployment_Test_Guide.md"
    echo ""
    echo "5. 如果啟用了Human Loop MCP，訪問Web界面："
    echo "   http://localhost:8096"
    echo ""
}

# 主函數
main() {
    echo ""
    info "開始快速設置和測試..."
    
    # 檢查工具
    if ! check_tools; then
        error "工具檢查失敗，請安裝必要工具後重試"
        exit 1
    fi
    
    # 檢查連接
    if ! check_connection; then
        error "連接檢查失敗，請建立SSH port forwarding後重試"
        exit 1
    fi
    
    # 執行快速測試
    if ! run_quick_test; then
        error "快速測試失敗，請檢查PowerAutomation服務狀態"
        exit 1
    fi
    
    # 顯示下一步
    show_next_steps
    
    success "快速開始完成！"
}

# 執行主函數
main "$@"

