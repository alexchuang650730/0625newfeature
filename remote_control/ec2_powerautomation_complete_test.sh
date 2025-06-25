#!/bin/bash

# PowerAutomation EC2服务器完整测试套件
# 在EC2服务器18.212.97.173上执行
# 验证VSIX部署、Enhanced VSCode Installer MCP以及Human Loop MCP集成

echo "🚀 PowerAutomation EC2服务器完整测试套件"
echo "========================================"

# 设置变量
TEST_TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="ec2_powerautomation_test_${TEST_TIMESTAMP}.log"
REPORT_FILE="ec2_powerautomation_report_${TEST_TIMESTAMP}.json"
POWERAUTOMATION_LOCAL_DIR="/home/ec2-user/aicore0624/PowerAutomation_local"
POWERAUTOMATION_DIR="/home/ec2-user/aicore0624/PowerAutomation"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 日志函数
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

# 初始化测试报告
init_report() {
    cat > "$REPORT_FILE" << EOF
{
    "test_info": {
        "timestamp": "$TEST_TIMESTAMP",
        "server": "EC2-18.212.97.173",
        "test_type": "complete_powerautomation_validation",
        "tester": "Manus AI Agent"
    },
    "test_results": {}
}
EOF
}

# 更新测试报告
update_report() {
    local test_name="$1"
    local result="$2"
    local status="$3"
    
    if command -v jq &> /dev/null; then
        jq ".test_results[\"$test_name\"] = {\"result\": $result, \"status\": \"$status\", \"timestamp\": \"$(date -Iseconds)\"}" "$REPORT_FILE" > "${REPORT_FILE}.tmp" && mv "${REPORT_FILE}.tmp" "$REPORT_FILE"
    fi
}

# 测试1: 系统环境检查
test_system_environment() {
    echo ""
    info "🔍 测试1: 系统环境检查"
    echo "========================"
    
    log "检查系统信息"
    uname -a | tee -a "$LOG_FILE"
    
    log "检查磁盘空间"
    df -h | tee -a "$LOG_FILE"
    
    log "检查内存使用"
    free -h | tee -a "$LOG_FILE"
    
    log "检查Python版本"
    python3 --version | tee -a "$LOG_FILE"
    
    success "系统环境检查完成"
    update_report "system_environment" "\"$(uname -a)\"" "success"
    return 0
}

# 测试2: PowerAutomation Local MCP状态检查
test_powerautomation_local_status() {
    echo ""
    info "🔧 测试2: PowerAutomation Local MCP状态检查"
    echo "==========================================="
    
    # 检查PowerAutomation Local目录
    if [ -d "$POWERAUTOMATION_LOCAL_DIR" ]; then
        success "PowerAutomation Local目录存在"
        log "目录路径: $POWERAUTOMATION_LOCAL_DIR"
        
        cd "$POWERAUTOMATION_LOCAL_DIR"
        
        # 检查虚拟环境
        if [ -d "powerautomation_env" ]; then
            success "虚拟环境已创建"
            
            # 检查虚拟环境中的包
            source powerautomation_env/bin/activate
            pip list | head -10 | tee -a "$LOG_FILE"
            
        else
            warning "虚拟环境不存在，尝试创建"
            ./install.sh | tee -a "$LOG_FILE"
        fi
        
        # 检查主要文件
        local files=("powerautomation_local_mcp.py" "mcp_server.py" "start.sh")
        for file in "${files[@]}"; do
            if [ -f "$file" ]; then
                success "文件存在: $file"
            else
                error "文件缺失: $file"
            fi
        done
        
        update_report "powerautomation_local_status" "\"directory_exists\"" "success"
    else
        error "PowerAutomation Local目录不存在: $POWERAUTOMATION_LOCAL_DIR"
        update_report "powerautomation_local_status" "\"directory_missing\"" "failed"
        return 1
    fi
    
    return 0
}

# 测试3: 启动PowerAutomation Local MCP服务
test_start_powerautomation_service() {
    echo ""
    info "🚀 测试3: 启动PowerAutomation Local MCP服务"
    echo "==========================================="
    
    cd "$POWERAUTOMATION_LOCAL_DIR"
    
    # 检查是否已经在运行
    local existing_process=$(ps aux | grep powerautomation_local_mcp.py | grep -v grep)
    if [ -n "$existing_process" ]; then
        warning "PowerAutomation服务已在运行"
        log "现有进程: $existing_process"
    else
        info "启动PowerAutomation Local MCP服务"
        
        # 启动服务
        nohup ./start.sh > powerautomation_service.log 2>&1 &
        local service_pid=$!
        
        log "服务启动，PID: $service_pid"
        
        # 等待服务启动
        sleep 10
        
        # 检查服务状态
        if ps -p $service_pid > /dev/null; then
            success "PowerAutomation服务启动成功"
        else
            error "PowerAutomation服务启动失败"
            log "检查日志:"
            tail -20 powerautomation_service.log | tee -a "$LOG_FILE"
            return 1
        fi
    fi
    
    # 检查端口监听
    local port_check=$(netstat -tlnp | grep 8394)
    if [ -n "$port_check" ]; then
        success "8394端口正在监听"
        log "端口信息: $port_check"
        update_report "powerautomation_service" "\"running_on_8394\"" "success"
    else
        warning "8394端口未监听，检查其他可能的端口"
        netstat -tlnp | grep python | tee -a "$LOG_FILE"
        update_report "powerautomation_service" "\"port_8394_not_listening\"" "warning"
    fi
    
    return 0
}

# 测试4: PowerAutomation API端点测试
test_powerautomation_api() {
    echo ""
    info "🌐 测试4: PowerAutomation API端点测试"
    echo "===================================="
    
    # 尝试不同的端口和URL
    local urls=(
        "http://localhost:8394"
        "http://localhost:8394/health"
        "http://localhost:8394/api"
        "http://127.0.0.1:8394"
    )
    
    for url in "${urls[@]}"; do
        info "测试URL: $url"
        local response=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null)
        
        if [ "$response" = "200" ]; then
            success "URL可访问: $url (HTTP $response)"
            
            # 获取响应内容
            local content=$(curl -s "$url" 2>/dev/null)
            if [ -n "$content" ]; then
                log "响应内容: $content"
                echo "$content" | jq . 2>/dev/null || echo "$content"
            fi
            
            update_report "powerautomation_api" "\"$url accessible\"" "success"
            return 0
        else
            warning "URL不可访问: $url (HTTP $response)"
        fi
    done
    
    error "所有PowerAutomation API端点都不可访问"
    update_report "powerautomation_api" "\"all_endpoints_inaccessible\"" "failed"
    return 1
}

# 测试5: Enhanced VSCode Installer MCP测试
test_enhanced_vscode_installer_mcp() {
    echo ""
    info "🔌 测试5: Enhanced VSCode Installer MCP测试"
    echo "=========================================="
    
    cd "$POWERAUTOMATION_DIR"
    
    # 检查Enhanced VSCode Installer MCP文件
    local mcp_files=$(find . -name "*vscode*" -o -name "*vsix*" | head -10)
    if [ -n "$mcp_files" ]; then
        success "找到VSCode相关文件"
        echo "$mcp_files" | tee -a "$LOG_FILE"
    else
        warning "未找到VSCode相关文件"
    fi
    
    # 检查组件目录
    if [ -d "components" ]; then
        local vscode_components=$(find components -name "*vscode*" -o -name "*vsix*")
        if [ -n "$vscode_components" ]; then
            success "找到VSCode组件"
            echo "$vscode_components" | tee -a "$LOG_FILE"
        fi
    fi
    
    # 尝试API测试
    local vscode_api_urls=(
        "http://localhost:8394/api/mcp/enhanced_vscode_installer"
        "http://localhost:8394/api/vsix/deploy"
        "http://localhost:8394/api/components"
    )
    
    for url in "${vscode_api_urls[@]}"; do
        info "测试VSCode API: $url"
        local response=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null)
        
        if [ "$response" = "200" ] || [ "$response" = "405" ]; then
            success "VSCode API端点可访问: $url (HTTP $response)"
            update_report "enhanced_vscode_installer_mcp" "\"$url accessible\"" "success"
            return 0
        fi
    done
    
    warning "Enhanced VSCode Installer MCP API端点不可访问"
    update_report "enhanced_vscode_installer_mcp" "\"api_endpoints_inaccessible\"" "warning"
    return 0
}

# 测试6: Human Loop MCP集成测试
test_human_loop_mcp() {
    echo ""
    info "🤝 测试6: Human Loop MCP集成测试"
    echo "==============================="
    
    # 检查8096端口（Human Loop MCP默认端口）
    local human_loop_process=$(netstat -tlnp | grep 8096)
    if [ -n "$human_loop_process" ]; then
        success "Human Loop MCP服务正在运行"
        log "端口信息: $human_loop_process"
        
        # 测试Human Loop MCP API
        local human_loop_urls=(
            "http://localhost:8096"
            "http://localhost:8096/api/health"
            "http://localhost:8096/api/sessions"
        )
        
        for url in "${human_loop_urls[@]}"; do
            info "测试Human Loop API: $url"
            local response=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null)
            
            if [ "$response" = "200" ]; then
                success "Human Loop API可访问: $url"
                
                # 获取响应内容
                local content=$(curl -s "$url" 2>/dev/null)
                if [ -n "$content" ]; then
                    log "Human Loop响应: $content"
                    echo "$content" | jq . 2>/dev/null || echo "$content"
                fi
                
                update_report "human_loop_mcp" "\"service_running_and_accessible\"" "success"
                return 0
            fi
        done
        
        warning "Human Loop MCP服务运行但API不可访问"
        update_report "human_loop_mcp" "\"service_running_api_inaccessible\"" "warning"
    else
        warning "Human Loop MCP服务未运行"
        update_report "human_loop_mcp" "\"service_not_running\"" "warning"
    fi
    
    return 0
}

# 测试7: VSIX部署功能测试
test_vsix_deployment() {
    echo ""
    info "🚀 测试7: VSIX部署功能测试"
    echo "=========================="
    
    # 创建测试VSIX部署请求
    local test_data='{
        "vsix_path": "/test/sample-extension.vsix",
        "target_environment": "development",
        "deployment_mode": "test",
        "force_install": false,
        "backup_existing": true,
        "validate_before_install": true
    }'
    
    info "测试VSIX部署API"
    log "测试数据: $test_data"
    
    # 尝试不同的VSIX部署端点
    local vsix_endpoints=(
        "http://localhost:8394/api/vsix/deploy"
        "http://localhost:8394/vsix/deploy"
        "http://localhost:8394/deploy"
    )
    
    for endpoint in "${vsix_endpoints[@]}"; do
        info "测试VSIX部署端点: $endpoint"
        
        local response=$(curl -s -X POST \
            -H "Content-Type: application/json" \
            -d "$test_data" \
            "$endpoint" 2>/dev/null)
        
        local status_code=$(curl -s -o /dev/null -w "%{http_code}" -X POST \
            -H "Content-Type: application/json" \
            -d "$test_data" \
            "$endpoint" 2>/dev/null)
        
        if [ "$status_code" = "200" ] || [ "$status_code" = "202" ]; then
            success "VSIX部署端点响应成功: $endpoint (HTTP $status_code)"
            log "部署响应: $response"
            echo "$response" | jq . 2>/dev/null || echo "$response"
            update_report "vsix_deployment" "\"$endpoint successful\"" "success"
            return 0
        elif [ "$status_code" = "405" ]; then
            info "VSIX部署端点存在但方法不允许: $endpoint (HTTP $status_code)"
        else
            warning "VSIX部署端点不可访问: $endpoint (HTTP $status_code)"
        fi
    done
    
    warning "所有VSIX部署端点都不可访问"
    update_report "vsix_deployment" "\"all_endpoints_inaccessible\"" "warning"
    return 0
}

# 测试8: 综合集成测试
test_comprehensive_integration() {
    echo ""
    info "🎯 测试8: 综合集成测试"
    echo "======================"
    
    info "执行综合系统状态检查"
    
    # 检查所有相关进程
    log "所有Python进程:"
    ps aux | grep python | grep -v grep | tee -a "$LOG_FILE"
    
    # 检查所有监听端口
    log "所有监听端口:"
    netstat -tlnp | grep LISTEN | tee -a "$LOG_FILE"
    
    # 检查系统资源使用
    log "系统资源使用:"
    top -bn1 | head -20 | tee -a "$LOG_FILE"
    
    # 生成系统状态摘要
    local total_processes=$(ps aux | grep -E '(powerautomation|mcp|aicore)' | grep -v grep | wc -l)
    local listening_ports=$(netstat -tlnp | grep LISTEN | wc -l)
    local python_processes=$(ps aux | grep python | grep -v grep | wc -l)
    
    log "系统状态摘要:"
    log "- PowerAutomation/MCP相关进程: $total_processes"
    log "- 监听端口总数: $listening_ports"
    log "- Python进程总数: $python_processes"
    
    success "综合集成测试完成"
    update_report "comprehensive_integration" "{\"processes\": $total_processes, \"ports\": $listening_ports, \"python_processes\": $python_processes}" "success"
    
    return 0
}

# 生成最终报告
generate_final_report() {
    echo ""
    info "📊 生成最终测试报告"
    echo "==================="
    
    # 添加总结信息到报告
    if command -v jq &> /dev/null; then
        jq ".summary = {
            \"total_tests\": 8,
            \"log_file\": \"$LOG_FILE\",
            \"report_file\": \"$REPORT_FILE\",
            \"test_completion_time\": \"$(date -Iseconds)\",
            \"server_info\": \"$(uname -a)\",
            \"recommendations\": [
                \"检查PowerAutomation Local MCP服务状态\",
                \"验证8394端口监听状态\",
                \"确认Human Loop MCP集成配置\",
                \"测试实际VSIX文件部署功能\"
            ]
        }" "$REPORT_FILE" > "${REPORT_FILE}.tmp" && mv "${REPORT_FILE}.tmp" "$REPORT_FILE"
    fi
    
    success "测试报告已生成: $REPORT_FILE"
    success "详细日志已保存: $LOG_FILE"
    
    # 显示报告摘要
    if command -v jq &> /dev/null; then
        echo ""
        info "测试报告摘要:"
        jq '.summary' "$REPORT_FILE" 2>/dev/null || cat "$REPORT_FILE"
    fi
}

# 主函数
main() {
    log "开始PowerAutomation EC2服务器完整测试套件"
    
    # 初始化
    init_report
    
    # 执行测试
    local failed_tests=0
    
    test_system_environment || ((failed_tests++))
    test_powerautomation_local_status || ((failed_tests++))
    test_start_powerautomation_service || ((failed_tests++))
    test_powerautomation_api || ((failed_tests++))
    test_enhanced_vscode_installer_mcp || ((failed_tests++))
    test_human_loop_mcp || ((failed_tests++))
    test_vsix_deployment || ((failed_tests++))
    test_comprehensive_integration || ((failed_tests++))
    
    # 生成报告
    generate_final_report
    
    # 显示总结
    echo ""
    echo "🎯 测试总结"
    echo "============"
    if [ $failed_tests -eq 0 ]; then
        success "所有测试完成！"
    else
        warning "$failed_tests 个测试遇到问题，请查看详细日志"
    fi
    
    echo ""
    echo "📄 查看测试报告:"
    echo "cat $REPORT_FILE | jq ."
    echo ""
    echo "📝 查看详细日志:"
    echo "cat $LOG_FILE"
    
    log "PowerAutomation EC2服务器完整测试套件完成"
}

# 执行主函数
main "$@"

