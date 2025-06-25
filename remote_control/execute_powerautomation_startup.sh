#!/bin/bash

# SmartUI Fusion 遠端控制系統最終執行腳本
# 用於測試完整的 EC2 到 Mac 部署流程

echo "🎯 SmartUI Fusion 遠端控制系統測試"
echo "=================================="

# 測試 SSH 連接
test_ssh() {
    echo "🔗 測試 SSH 連接..."
    if ssh -o ConnectTimeout=10 ec2_remote_via_vpn "echo 'SSH 連接成功'" 2>/dev/null; then
        echo "✅ SSH 連接正常"
        return 0
    else
        echo "❌ SSH 連接失敗"
        echo "💡 請檢查:"
        echo "   1. VPN 是否連接"
        echo "   2. SOCKS5 代理是否運行 (127.0.0.1:7897)"
        echo "   3. Mac 端 SSH 服務是否啟用"
        return 1
    fi
}

# 檢查 Mac 端配置
check_mac_setup() {
    echo "🔍 檢查 Mac 端配置..."
    
    # 檢查部署目錄
    if ssh ec2_remote_via_vpn "test -d ~/vsix_deploy" 2>/dev/null; then
        echo "✅ Mac 端部署目錄存在"
    else
        echo "❌ Mac 端部署目錄不存在"
        echo "💡 請先在 Mac 端執行配置腳本:"
        echo "   scp ec2_remote_via_vpn:/home/ubuntu/mac_ssh_setup.sh ~/mac_ssh_setup.sh"
        echo "   chmod +x ~/mac_ssh_setup.sh && ~/mac_ssh_setup.sh"
        return 1
    fi
    
    # 檢查 VS Code
    if ssh ec2_remote_via_vpn "command -v code" 2>/dev/null; then
        echo "✅ VS Code 命令行工具已安裝"
    else
        echo "❌ VS Code 命令行工具未安裝"
        echo "💡 請在 Mac 的 VS Code 中執行: Shell Command: Install 'code' command in PATH"
        return 1
    fi
    
    return 0
}

# 測試文件傳輸
test_file_transfer() {
    echo "📁 測試文件傳輸..."
    
    # 創建測試文件
    echo "Test file from EC2 at $(date)" > /tmp/test_transfer.txt
    
    # 傳輸到 Mac
    if scp /tmp/test_transfer.txt ec2_remote_via_vpn:~/vsix_deploy/ 2>/dev/null; then
        echo "✅ 文件傳輸成功"
        
        # 驗證文件存在
        if ssh ec2_remote_via_vpn "cat ~/vsix_deploy/test_transfer.txt" 2>/dev/null; then
            echo "✅ 文件內容驗證成功"
        else
            echo "❌ 文件內容驗證失敗"
            return 1
        fi
        
        # 清理測試文件
        ssh ec2_remote_via_vpn "rm -f ~/vsix_deploy/test_transfer.txt" 2>/dev/null
        rm -f /tmp/test_transfer.txt
        
        return 0
    else
        echo "❌ 文件傳輸失敗"
        return 1
    fi
}

# 測試 VSIX 構建
test_vsix_build() {
    echo "🔧 測試 VSIX 構建..."
    
    # 檢查項目目錄
    if [ ! -d "/home/ubuntu/0625newfeature/vscode-extension" ]; then
        echo "❌ VS Code 擴展項目不存在"
        echo "💡 請確保項目已正確設置"
        return 1
    fi
    
    # 檢查 package.json
    if [ ! -f "/home/ubuntu/0625newfeature/vscode-extension/package.json" ]; then
        echo "❌ package.json 不存在"
        return 1
    fi
    
    echo "✅ VS Code 擴展項目結構正常"
    return 0
}

# 執行完整測試
run_full_test() {
    echo "🚀 執行完整的遠端部署測試..."
    
    # 使用部署腳本進行測試
    if /home/ubuntu/auto_deploy_vsix.sh; then
        echo "✅ 完整部署測試成功!"
        return 0
    else
        echo "❌ 完整部署測試失敗"
        return 1
    fi
}

# 顯示系統狀態
show_system_status() {
    echo "📊 系統狀態摘要"
    echo "=================="
    
    echo "🖥️  EC2 端:"
    echo "   - 操作系統: $(uname -s)"
    echo "   - 當前用戶: $(whoami)"
    echo "   - 工作目錄: $(pwd)"
    echo "   - Node.js: $(node --version 2>/dev/null || echo '未安裝')"
    echo "   - npm: $(npm --version 2>/dev/null || echo '未安裝')"
    
    echo ""
    echo "🍎 Mac 端:"
    if ssh ec2_remote_via_vpn "uname -a && whoami" 2>/dev/null; then
        echo "   - VS Code: $(ssh ec2_remote_via_vpn 'code --version 2>/dev/null | head -1' || echo '未安裝')"
        echo "   - 部署目錄: $(ssh ec2_remote_via_vpn 'test -d ~/vsix_deploy && echo "存在" || echo "不存在"')"
    else
        echo "   - 連接失敗"
    fi
    
    echo ""
    echo "🔗 網絡連接:"
    echo "   - SSH 配置: ec2_remote_via_vpn"
    echo "   - 代理: SOCKS5://127.0.0.1:7897"
}

# 主執行流程
main() {
    echo "開始系統測試..."
    echo ""
    
    # 顯示系統狀態
    show_system_status
    echo ""
    
    # 執行測試步驟
    local all_passed=true
    
    if ! test_ssh; then
        all_passed=false
    fi
    echo ""
    
    if ! check_mac_setup; then
        all_passed=false
    fi
    echo ""
    
    if ! test_file_transfer; then
        all_passed=false
    fi
    echo ""
    
    if ! test_vsix_build; then
        all_passed=false
    fi
    echo ""
    
    # 如果基礎測試都通過，執行完整測試
    if [ "$all_passed" = true ]; then
        echo "🎉 基礎測試全部通過!"
        echo ""
        
        read -p "是否執行完整的 VSIX 部署測試? (y/N): " confirm
        if [[ $confirm =~ ^[Yy]$ ]]; then
            run_full_test
        fi
    else
        echo "❌ 基礎測試失敗，請修復問題後重試"
        echo ""
        echo "🔧 修復建議:"
        echo "1. 確保 VPN 連接正常"
        echo "2. 在 Mac 端執行配置腳本"
        echo "3. 檢查 SSH 密鑰權限"
        echo "4. 確認防火牆設置"
    fi
    
    echo ""
    echo "📋 快速命令參考:"
    echo "   啟動系統: /home/ubuntu/start_powerautomation_mcp.sh"
    echo "   直接部署: /home/ubuntu/auto_deploy_vsix.sh"
    echo "   檢查狀態: /home/ubuntu/auto_deploy_vsix.sh --status"
    echo "   查看幫助: cat /home/ubuntu/quick_start_commands.txt"
}

# 執行主函數
main "$@"

