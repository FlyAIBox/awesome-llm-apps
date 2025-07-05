#!/usr/bin/env python3
"""
配置测试脚本
用于验证 secrets.toml 文件和环境变量的读取功能
"""

import os
import sys
import streamlit as st
from pathlib import Path

def test_config_reading():
    """测试配置文件读取功能"""
    print("=== 配置文件读取测试 ===")
    
    # 检查 secrets.toml 文件是否存在
    secrets_file = Path(".streamlit/secrets.toml")
    if secrets_file.exists():
        print(f"✓ secrets.toml 文件存在: {secrets_file.absolute()}")
        
        # 读取文件内容
        with open(secrets_file, 'r', encoding='utf-8') as f:
            content = f.read()
            print(f"文件内容:\n{content}")
    else:
        print(f"✗ secrets.toml 文件不存在: {secrets_file.absolute()}")
    
    # 检查环境变量
    print("\n=== 环境变量检查 ===")
    env_vars = ["OPENAI_API_KEY", "OPENAI_BASE_URL", "SERPAPI_KEY"]
    for var in env_vars:
        value = os.getenv(var)
        if value:
            print(f"✓ {var}: {value[:10]}...")
        else:
            print(f"✗ {var}: 未设置")
    
    # 尝试使用 streamlit secrets
    print("\n=== Streamlit Secrets 测试 ===")
    try:
        # 这里需要在 streamlit 环境中运行才能正常工作
        if hasattr(st, 'secrets'):
            for key in ["OPENAI_API_KEY", "OPENAI_BASE_URL", "SERPAPI_KEY"]:
                if key in st.secrets:
                    value = st.secrets[key]
                    print(f"✓ {key}: {value[:10]}...")
                else:
                    print(f"✗ {key}: 未在 secrets 中找到")
        else:
            print("⚠️ 当前不在 Streamlit 环境中，无法测试 st.secrets")
    except Exception as e:
        print(f"✗ 读取 secrets 时出错: {e}")

if __name__ == "__main__":
    test_config_reading() 