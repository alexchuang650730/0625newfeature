#!/bin/bash

# PowerAutomation Local MCP VSIX部署測試腳本
# 通過SSH Port Forwarding連接測試
# 
# 使用方法:
# 1. 確保SSH port forwarding已建立: ssh ec2_remote_via_vpn -L 8080:localhost:8394
# 2. 在Mac終端中執行此腳本: ./test_powerautomation_vsix_deployment.sh

echo "🚀 PowerAutomation Local MCP VSIX部署測試"
echo "=========================================="

# 設置變量
LOCAL_PORT=8080
REMOTE_PORT=8394
POWERAUTOMATION_URL="http://localhost:${LOCAL_PORT}"
TEST_TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="powerautomation_vsix_test_${TEST_TIMESTAMP}.log"

# 創建日誌函數
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "開始PowerAutomation Local MCP VSIX部署測試"
log "本地端口: $LOCAL_PORT"
log "遠程端口: $REMOTE_PORT"
log "PowerAutomation URL: $POWERAUTOMATION_URL"

# 1. 驗證SSH Port Forwarding連接
echo ""
echo "📡 步驟1: 驗證SSH Port Forwarding連接"
echo "----------------------------------------"

log "測試連接到 $POWERAUTOMATION_URL"
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$POWERAUTOMATION_URL" 2>/dev/null)

if [ "$HTTP_STATUS" = "000" ]; then
    log "❌ 錯誤: 無法連接到PowerAutomation服務"
    log "請確認:"
    log "1. SSH port forwarding已建立: ssh ec2_remote_via_vpn -L 8080:localhost:8394"
    log "2. EC2上的PowerAutomation Local MCP服務正在運行"
    exit 1
elif [ "$HTTP_STATUS" = "200" ]; then
    log "✅ 成功連接到PowerAutomation服務 (HTTP $HTTP_STATUS)"
else
    log "⚠️  連接到PowerAutomation服務，但返回HTTP $HTTP_STATUS"
fi

# 2. 檢查PowerAutomation Local MCP狀態
echo ""
echo "🔍 步驟2: 檢查PowerAutomation Local MCP狀態"
echo "--------------------------------------------"

log "檢查PowerAutomation健康狀態"
HEALTH_RESPONSE=$(curl -s "$POWERAUTOMATION_URL/health" 2>/dev/null)

if [ $? -eq 0 ] && [ -n "$HEALTH_RESPONSE" ]; then
    log "✅ PowerAutomation健康檢查成功"
    log "健康狀態響應: $HEALTH_RESPONSE"
    echo "$HEALTH_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$HEALTH_RESPONSE"
else
    log "⚠️  PowerAutomation健康檢查失敗或無響應"
fi

# 3. 檢查VSIX部署端點
echo ""
echo "🔧 步驟3: 檢查VSIX部署端點"
echo "----------------------------"

log "檢查VSIX部署API端點"
VSIX_ENDPOINT="$POWERAUTOMATION_URL/api/vsix/deploy"
VSIX_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$VSIX_ENDPOINT" 2>/dev/null)

if [ "$VSIX_STATUS" = "200" ] || [ "$VSIX_STATUS" = "405" ]; then
    log "✅ VSIX部署端點可訪問 (HTTP $VSIX_STATUS)"
else
    log "⚠️  VSIX部署端點狀態: HTTP $VSIX_STATUS"
fi

# 4. 測試VSIX部署功能
echo ""
echo "🚀 步驟4: 測試VSIX部署功能"
echo "----------------------------"

# 創建測試VSIX部署請求
TEST_VSIX_DATA='{
    "vsix_path": "/test/sample.vsix",
    "target_environment": "development",
    "deployment_mode": "test",
    "force_install": false,
    "backup_existing": true
}'

log "發送測試VSIX部署請求"
log "測試數據: $TEST_VSIX_DATA"

DEPLOY_RESPONSE=$(curl -s -X POST \
    -H "Content-Type: application/json" \
    -d "$TEST_VSIX_DATA" \
    "$VSIX_ENDPOINT" 2>/dev/null)

if [ $? -eq 0 ] && [ -n "$DEPLOY_RESPONSE" ]; then
    log "✅ VSIX部署請求發送成功"
    log "部署響應: $DEPLOY_RESPONSE"
    echo "$DEPLOY_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$DEPLOY_RESPONSE"
else
    log "❌ VSIX部署請求失敗"
fi

# 5. 檢查PowerAutomation組件狀態
echo ""
echo "📊 步驟5: 檢查PowerAutomation組件狀態"
echo "--------------------------------------"

log "檢查PowerAutomation組件列表"
COMPONENTS_RESPONSE=$(curl -s "$POWERAUTOMATION_URL/api/components" 2>/dev/null)

if [ $? -eq 0 ] && [ -n "$COMPONENTS_RESPONSE" ]; then
    log "✅ 組件狀態檢查成功"
    log "組件響應: $COMPONENTS_RESPONSE"
    echo "$COMPONENTS_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$COMPONENTS_RESPONSE"
else
    log "⚠️  組件狀態檢查失敗或無響應"
fi

# 6. 測試Enhanced VSCode Installer MCP
echo ""
echo "🔌 步驟6: 測試Enhanced VSCode Installer MCP"
echo "-------------------------------------------"

log "檢查Enhanced VSCode Installer MCP狀態"
VSCODE_MCP_ENDPOINT="$POWERAUTOMATION_URL/api/mcp/enhanced_vscode_installer"
VSCODE_MCP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$VSCODE_MCP_ENDPOINT" 2>/dev/null)

if [ "$VSCODE_MCP_STATUS" = "200" ]; then
    log "✅ Enhanced VSCode Installer MCP可訪問"
    
    # 獲取MCP詳細信息
    VSCODE_MCP_INFO=$(curl -s "$VSCODE_MCP_ENDPOINT" 2>/dev/null)
    if [ -n "$VSCODE_MCP_INFO" ]; then
        log "Enhanced VSCode Installer MCP信息: $VSCODE_MCP_INFO"
        echo "$VSCODE_MCP_INFO" | python3 -m json.tool 2>/dev/null || echo "$VSCODE_MCP_INFO"
    fi
else
    log "⚠️  Enhanced VSCode Installer MCP狀態: HTTP $VSCODE_MCP_STATUS"
fi

# 7. 生成測試報告
echo ""
echo "📋 步驟7: 生成測試報告"
echo "----------------------"

REPORT_FILE="powerautomation_vsix_deployment_report_${TEST_TIMESTAMP}.json"

cat > "$REPORT_FILE" << EOF
{
    "test_timestamp": "$TEST_TIMESTAMP",
    "test_configuration": {
        "local_port": $LOCAL_PORT,
        "remote_port": $REMOTE_PORT,
        "powerautomation_url": "$POWERAUTOMATION_URL"
    },
    "test_results": {
        "ssh_port_forwarding": {
            "status": "$HTTP_STATUS",
            "success": $([ "$HTTP_STATUS" = "200" ] && echo "true" || echo "false")
        },
        "powerautomation_health": {
            "response": $(echo "$HEALTH_RESPONSE" | jq -c . 2>/dev/null || echo "\"$HEALTH_RESPONSE\""),
            "success": $([ -n "$HEALTH_RESPONSE" ] && echo "true" || echo "false")
        },
        "vsix_deployment_endpoint": {
            "status": "$VSIX_STATUS",
            "success": $([ "$VSIX_STATUS" = "200" ] || [ "$VSIX_STATUS" = "405" ] && echo "true" || echo "false")
        },
        "vsix_deployment_test": {
            "response": $(echo "$DEPLOY_RESPONSE" | jq -c . 2>/dev/null || echo "\"$DEPLOY_RESPONSE\""),
            "success": $([ -n "$DEPLOY_RESPONSE" ] && echo "true" || echo "false")
        },
        "enhanced_vscode_installer_mcp": {
            "status": "$VSCODE_MCP_STATUS",
            "info": $(echo "$VSCODE_MCP_INFO" | jq -c . 2>/dev/null || echo "\"$VSCODE_MCP_INFO\""),
            "success": $([ "$VSCODE_MCP_STATUS" = "200" ] && echo "true" || echo "false")
        }
    },
    "log_file": "$LOG_FILE"
}
EOF

log "✅ 測試完成！"
log "測試報告已保存到: $REPORT_FILE"
log "詳細日誌已保存到: $LOG_FILE"

echo ""
echo "📊 測試總結"
echo "============"
echo "📄 測試報告: $REPORT_FILE"
echo "📝 詳細日誌: $LOG_FILE"
echo ""
echo "🔍 查看測試報告:"
echo "cat $REPORT_FILE | python3 -m json.tool"
echo ""
echo "📖 查看詳細日誌:"
echo "cat $LOG_FILE"

# 顯示簡要結果
echo ""
echo "🎯 快速結果總覽:"
echo "SSH Port Forwarding: $([ "$HTTP_STATUS" = "200" ] && echo "✅ 成功" || echo "❌ 失敗")"
echo "PowerAutomation健康檢查: $([ -n "$HEALTH_RESPONSE" ] && echo "✅ 成功" || echo "❌ 失敗")"
echo "VSIX部署端點: $([ "$VSIX_STATUS" = "200" ] || [ "$VSIX_STATUS" = "405" ] && echo "✅ 可訪問" || echo "❌ 不可訪問")"
echo "Enhanced VSCode Installer MCP: $([ "$VSCODE_MCP_STATUS" = "200" ] && echo "✅ 可訪問" || echo "❌ 不可訪問")"

log "PowerAutomation Local MCP VSIX部署測試完成"

