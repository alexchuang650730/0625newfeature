#!/bin/bash

# SmartUI Fusion 遠端控制快速啟動腳本

echo "🚀 SmartUI Fusion 遠端控制系統"
echo "================================"

# 檢查當前位置
if [ ! -f "/home/ubuntu/auto_deploy_vsix.sh" ]; then
    echo "❌ 錯誤: 部署腳本不存在"
    exit 1
fi

show_menu() {
    echo ""
    echo "請選擇操作:"
    echo "1. 🔧 構建並部署 VSIX 到 Mac"
    echo "2. 📦 部署現有 VSIX 文件"
    echo "3. 📊 檢查 Mac 端狀態"
    echo "4. 🔗 測試 SSH 連接"
    echo "5. 📋 顯示 Mac 端配置腳本"
    echo "6. 🆘 顯示幫助信息"
    echo "0. 🚪 退出"
    echo ""
    read -p "請輸入選項 (0-6): " choice
}

test_ssh_connection() {
    echo "🔗 測試 SSH 連接到 Mac..."
    if ssh -o ConnectTimeout=5 ec2_remote_via_vpn "echo 'SSH 連接測試成功!'" 2>/dev/null; then
        echo "✅ SSH 連接正常"
        echo "📡 Mac 端信息:"
        ssh ec2_remote_via_vpn "uname -a && whoami && pwd"
    else
        echo "❌ SSH 連接失敗"
        echo "💡 請檢查:"
        echo "   - VPN 連接是否正常"
        echo "   - SSH 配置是否正確"
        echo "   - Mac 端 SSH 服務是否啟用"
    fi
}

show_mac_setup() {
    echo "📋 Mac 端配置腳本位置:"
    echo "   /home/ubuntu/mac_ssh_setup.sh"
    echo ""
    echo "🔧 在 Mac 端執行以下命令:"
    echo "   1. 複製腳本到 Mac:"
    echo "      scp ec2_remote_via_vpn:/home/ubuntu/mac_ssh_setup.sh ~/mac_ssh_setup.sh"
    echo ""
    echo "   2. 在 Mac 端執行:"
    echo "      chmod +x ~/mac_ssh_setup.sh"
    echo "      ~/mac_ssh_setup.sh"
    echo ""
    echo "   3. 啟動守護進程:"
    echo "      ~/vsix_deploy/remote_deploy_handler.sh --daemon"
}

show_help() {
    echo "🆘 SmartUI Fusion 遠端控制幫助"
    echo "================================"
    echo ""
    echo "📋 系統架構:"
    echo "   EC2 (開發環境) ←→ VPN ←→ Mac (VS Code)"
    echo ""
    echo "🔧 主要功能:"
    echo "   • 從 EC2 自動構建 VS Code 擴展"
    echo "   • 自動部署 VSIX 到 Mac"
    echo "   • 遠端安裝和更新擴展"
    echo "   • 實時狀態監控"
    echo ""
    echo "📁 重要文件:"
    echo "   • /home/ubuntu/auto_deploy_vsix.sh - EC2 端部署腳本"
    echo "   • /home/ubuntu/mac_ssh_setup.sh - Mac 端配置腳本"
    echo "   • /home/ubuntu/0625newfeature/vscode-extension - VS Code 擴展源碼"
    echo ""
    echo "🔗 SSH 配置:"
    echo "   Host: ec2_remote_via_vpn"
    echo "   通過 SOCKS5 代理連接"
    echo ""
    echo "💡 故障排除:"
    echo "   1. 檢查 VPN 連接"
    echo "   2. 測試 SSH 連接"
    echo "   3. 確認 Mac 端配置"
    echo "   4. 檢查防火牆設置"
}

# 主循環
while true; do
    show_menu
    
    case $choice in
        1)
            echo "🔧 開始構建並部署 VSIX..."
            /home/ubuntu/auto_deploy_vsix.sh
            ;;
        2)
            echo "📁 請輸入 VSIX 文件路徑:"
            read -p "VSIX 文件: " vsix_file
            if [ -f "$vsix_file" ]; then
                /home/ubuntu/auto_deploy_vsix.sh --vsix-file "$vsix_file"
            else
                echo "❌ 文件不存在: $vsix_file"
            fi
            ;;
        3)
            echo "📊 檢查 Mac 端狀態..."
            /home/ubuntu/auto_deploy_vsix.sh --status
            ;;
        4)
            test_ssh_connection
            ;;
        5)
            show_mac_setup
            ;;
        6)
            show_help
            ;;
        0)
            echo "👋 再見!"
            exit 0
            ;;
        *)
            echo "❌ 無效選項，請重新選擇"
            ;;
    esac
    
    echo ""
    read -p "按 Enter 繼續..."
done

