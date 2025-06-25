#!/bin/bash

# SmartUI Fusion 啟動腳本
# 用於快速啟動開發環境

set -e

echo "🚀 Starting SmartUI Fusion Development Environment..."

# 檢查 Python 版本
python_version=$(python3 --version 2>&1 | grep -oP '\d+\.\d+' | head -1)
required_version="3.11"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python $required_version or higher is required. Current version: $python_version"
    exit 1
fi

echo "✅ Python version check passed: $python_version"

# 檢查 Node.js 版本
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed"
    exit 1
fi

node_version=$(node --version | grep -oP '\d+' | head -1)
if [ "$node_version" -lt 18 ]; then
    echo "❌ Node.js 18 or higher is required"
    exit 1
fi

echo "✅ Node.js version check passed: $(node --version)"

# 創建虛擬環境（如果不存在）
if [ ! -d "venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv venv
fi

# 激活虛擬環境
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# 安裝 Python 依賴
echo "📥 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# 安裝 Node.js 依賴
echo "📥 Installing Node.js dependencies..."
npm install

# 創建必要的目錄
echo "📁 Creating necessary directories..."
mkdir -p logs
mkdir -p models
mkdir -p static
mkdir -p uploads

# 設置環境變量
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
export SMARTUI_FUSION_ENV="development"

# 檢查配置文件
if [ ! -f "config/app_config.json" ]; then
    echo "❌ Configuration file not found: config/app_config.json"
    exit 1
fi

echo "✅ Configuration file found"

# 啟動服務
echo "🎯 Starting SmartUI Fusion services..."

# 在後台啟動前端開發服務器
echo "🌐 Starting frontend development server..."
npm run dev:frontend &
FRONTEND_PID=$!

# 等待前端服務器啟動
sleep 3

# 啟動後端服務器
echo "⚡ Starting backend server..."
python3 -m src.main &
BACKEND_PID=$!

# 等待服務器啟動
sleep 5

# 檢查服務是否正常運行
echo "🔍 Checking service health..."

# 檢查後端健康狀態
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ Backend server is running on http://localhost:8000"
else
    echo "❌ Backend server failed to start"
    kill $FRONTEND_PID $BACKEND_PID 2>/dev/null || true
    exit 1
fi

# 檢查前端服務器
if curl -s http://localhost:5173 > /dev/null; then
    echo "✅ Frontend server is running on http://localhost:5173"
else
    echo "⚠️  Frontend server may still be starting..."
fi

echo ""
echo "🎉 SmartUI Fusion is now running!"
echo ""
echo "📊 Service URLs:"
echo "   Frontend:  http://localhost:5173"
echo "   Backend:   http://localhost:8000"
echo "   API Docs:  http://localhost:8000/docs"
echo "   Health:    http://localhost:8000/health"
echo ""
echo "🛠️  Development Commands:"
echo "   View logs:     tail -f logs/smartui_fusion.log"
echo "   Stop services: ./scripts/stop.sh"
echo "   Restart:       ./scripts/restart.sh"
echo ""

# 創建 PID 文件用於停止服務
echo $FRONTEND_PID > .frontend.pid
echo $BACKEND_PID > .backend.pid

echo "💡 Press Ctrl+C to stop all services"

# 等待用戶中斷
trap 'echo "🛑 Stopping services..."; kill $FRONTEND_PID $BACKEND_PID 2>/dev/null || true; rm -f .frontend.pid .backend.pid; echo "✅ Services stopped"; exit 0' INT

# 保持腳本運行
wait

