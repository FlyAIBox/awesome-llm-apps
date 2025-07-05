#!/bin/bash

# AI旅行助手 - 自动化环境设置脚本
# 适用于Ubuntu 22.04.5 LTS和Python 3.10.x

set -e  # 遇到错误时停止执行

echo "🛫 AI旅行助手环境设置脚本"
echo "=============================="

# 检查操作系统
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "✅ 检测到Linux系统"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    echo "✅ 检测到macOS系统"
else
    echo "⚠️  警告：未测试的操作系统，可能需要手动调整"
fi

# 检查Python版本
PYTHON_VERSION=$(python3 --version 2>&1 | grep -oP '\d+\.\d+' | head -1)
REQUIRED_VERSION="3.10"

if [[ $(echo "$PYTHON_VERSION >= $REQUIRED_VERSION" | bc -l) -eq 1 ]]; then
    echo "✅ Python版本 $PYTHON_VERSION 符合要求"
else
    echo "❌ 错误：需要Python $REQUIRED_VERSION或更高版本，当前版本：$PYTHON_VERSION"
    echo "请先安装Python 3.10："
    echo "  conda install python=3.10"
    echo "  或从 https://www.python.org/downloads/ 下载"
    exit 1
fi

# 检查conda是否安装
if command -v conda &> /dev/null; then
    echo "✅ 检测到conda"
    USE_CONDA=true
else
    echo "⚠️  未检测到conda，将使用pip和venv"
    USE_CONDA=false
fi

# 创建虚拟环境
ENV_NAME="ai-travel-agent"

if $USE_CONDA; then
    echo "📦 使用conda创建虚拟环境..."
    
    # 检查环境是否已存在
    if conda env list | grep -q "$ENV_NAME"; then
        echo "⚠️  环境 $ENV_NAME 已存在，是否要重新创建？(y/N)"
        read -r response
        if [[ "$response" =~ ^[Yy]$ ]]; then
            conda env remove -n "$ENV_NAME" -y
        else
            echo "使用现有环境 $ENV_NAME"
        fi
    fi
    
    if ! conda env list | grep -q "$ENV_NAME"; then
        conda create -n "$ENV_NAME" python=3.10 -y
    fi
    
    echo "激活conda环境："
    echo "  conda activate $ENV_NAME"
    
    # 激活环境
    eval "$(conda shell.bash hook)"
    conda activate "$ENV_NAME"
    
else
    echo "📦 使用venv创建虚拟环境..."
    
    if [ -d "$ENV_NAME" ]; then
        echo "⚠️  目录 $ENV_NAME 已存在，是否要重新创建？(y/N)"
        read -r response
        if [[ "$response" =~ ^[Yy]$ ]]; then
            rm -rf "$ENV_NAME"
        fi
    fi
    
    if [ ! -d "$ENV_NAME" ]; then
        python3 -m venv "$ENV_NAME"
    fi
    
    echo "激活venv环境："
    echo "  source $ENV_NAME/bin/activate"
    
    # 激活环境
    source "$ENV_NAME/bin/activate"
fi

# 升级pip
echo "⬆️  升级pip..."
pip install --upgrade pip

# 安装依赖包
echo "📚 安装项目依赖..."
pip install -r requirements.txt

# 验证安装
echo "🔍 验证安装..."

echo "检查Streamlit..."
if python -c "import streamlit; print('Streamlit版本:', streamlit.__version__)" 2>/dev/null; then
    echo "✅ Streamlit安装成功"
else
    echo "❌ Streamlit安装失败"
fi

echo "检查agno..."
if python -c "import agno; print('Agno安装成功')" 2>/dev/null; then
    echo "✅ Agno安装成功"
else
    echo "❌ Agno安装失败"
fi

echo "检查OpenAI..."
if python -c "import openai; print('OpenAI版本:', openai.__version__)" 2>/dev/null; then
    echo "✅ OpenAI安装成功"
else
    echo "❌ OpenAI安装失败"
fi

echo "检查SerpAPI..."
if python -c "from serpapi import GoogleSearch; print('SerpAPI安装成功')" 2>/dev/null; then
    echo "✅ SerpAPI安装成功"
else
    echo "❌ SerpAPI安装失败"
fi

# 创建配置目录
echo "📁 创建配置目录..."
mkdir -p .streamlit

# 检查是否需要创建secrets文件
if [ ! -f ".streamlit/secrets.toml" ]; then
    echo "🔐 创建API密钥配置文件..."
    cat > .streamlit/secrets.toml << EOF
# AI旅行助手 API密钥配置
# 请将下面的占位符替换为您的实际API密钥

# OpenAI API配置
OPENAI_API_KEY = "your-openai-api-key-here"

# SerpAPI配置  
SERPAPI_KEY = "your-serpapi-key-here"
EOF
    echo "📝 已创建 .streamlit/secrets.toml"
    echo "⚠️  请编辑此文件并添加您的实际API密钥"
else
    echo "✅ API密钥配置文件已存在"
fi

# 创建启动脚本
cat > start_app.sh << EOF
#!/bin/bash
# AI旅行助手启动脚本

echo "🛫 启动AI旅行助手..."

# 激活环境
if command -v conda &> /dev/null && conda env list | grep -q "$ENV_NAME"; then
    eval "\$(conda shell.bash hook)"
    conda activate "$ENV_NAME"
elif [ -d "$ENV_NAME" ]; then
    source "$ENV_NAME/bin/activate"
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
EOF

chmod +x start_app.sh

echo ""
echo "🎉 环境设置完成！"
echo "=============================="
echo ""
echo "📋 接下来的步骤："
echo "1. 配置API密钥："
echo "   编辑 .streamlit/secrets.toml 文件"
echo "   添加您的OpenAI和SerpAPI密钥"
echo ""
echo "2. 启动应用："
if $USE_CONDA; then
    echo "   conda activate $ENV_NAME"
else
    echo "   source $ENV_NAME/bin/activate"
fi
echo "   streamlit run travel_agent.py"
echo ""
echo "   或者直接运行："
echo "   ./start_app.sh"
echo ""
echo "3. 获取API密钥："
echo "   OpenAI: https://platform.openai.com/"
echo "   SerpAPI: https://serpapi.com/"
echo ""
echo "🌐 应用将在 http://localhost:8501 启动"
echo ""
echo "如有问题，请查看README-ZH.MD文档" 