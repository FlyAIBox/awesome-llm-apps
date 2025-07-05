#!/bin/bash
# AI旅行助手启动脚本

echo "🛫 启动AI旅行助手..."

# 激活环境
if command -v conda &> /dev/null && conda env list | grep -q "ai-travel-agent"; then
    eval "$(conda shell.bash hook)"
    conda activate "ai-travel-agent"
elif [ -d "ai-travel-agent" ]; then
    source "ai-travel-agent/bin/activate"
fi

# 检查API密钥配置
if [ ! -f ".streamlit/secrets.toml" ]; then
    echo "❌ 错误：未找到API密钥配置文件"
    echo "请先配置 .streamlit/secrets.toml 文件"
    exit 1
fi

# 启动应用
echo "🚀 启动Streamlit应用..."
streamlit run travel_agent.py
