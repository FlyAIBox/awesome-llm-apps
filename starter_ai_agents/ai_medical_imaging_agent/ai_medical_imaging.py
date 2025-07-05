#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
医疗影像诊断智能代理 (Medical Imaging Diagnosis Agent)

项目目的:
    基于 Agno 框架和 Gemini 2.0 Flash 模型，构建一个智能医疗影像分析系统，
    为医护人员和研究人员提供 AI 辅助的医疗影像诊断服务。

主要功能:
    - 多模态医疗影像分析（X光、CT、MRI、超声波等）
    - 智能异常检测和诊断建议
    - 自动生成结构化诊断报告
    - 实时文献检索和参考资料
    - 患者友好的解释说明

技术架构:
    ┌─────────────────────────────────────────────────────┐
    │                 用户界面层 (Streamlit)               │
    ├─────────────────────────────────────────────────────┤
    │              图像处理层 (Pillow)                    │
    ├─────────────────────────────────────────────────────┤
    │           AI代理层 (Agno Framework)                 │
    │  ┌─────────────────┐  ┌─────────────────────────┐   │
    │  │ Gemini 2.0 Flash│  │   DuckDuckGo Search    │   │
    │  │    AI 模型      │  │      搜索工具          │   │
    │  └─────────────────┘  └─────────────────────────┘   │
    └─────────────────────────────────────────────────────┘

核心组件:
    1. 图像上传与预处理模块
    2. AI 驱动的医疗影像分析引擎
    3. 智能诊断报告生成器
    4. 外部医学文献检索系统
    5. 交互式Web用户界面

作者: AI Medical Imaging Team
版本: 1.0.0
更新日期: 2024
许可证: MIT License
"""

import os
from PIL import Image as PILImage
from agno.agent import Agent
from agno.models.google import Gemini
import streamlit as st
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.media import Image as AgnoImage

# ========================= 会话状态管理 =========================
# 初始化 Google API 密钥的会话状态
# 用于在整个应用会话中保持API密钥的持久化存储
if "GOOGLE_API_KEY" not in st.session_state:
    st.session_state.GOOGLE_API_KEY = None

# ========================= 侧边栏配置界面 =========================
with st.sidebar:
    st.title("ℹ️ 配置信息")
    
    # API 密钥配置模块
    # 如果用户尚未配置API密钥，显示输入框
    if not st.session_state.GOOGLE_API_KEY:
        api_key = st.text_input(
            "请输入您的 Google API 密钥:",
            type="password",  # 密码类型输入，保护隐私
            help="从 Google AI Studio 获取您的 API 密钥"
        )
        st.caption(
            "从 [Google AI Studio]"
            "(https://aistudio.google.com/apikey) 获取您的 API 密钥 🔑"
        )
        # 当用户输入API密钥后，保存到会话状态并重新运行应用
        if api_key:
            st.session_state.GOOGLE_API_KEY = api_key
            st.success("API 密钥已保存！")
            st.rerun()
    else:
        # 如果已配置API密钥，显示成功状态和重置选项
        st.success("API 密钥已配置")
        if st.button("🔄 重置 API 密钥"):
            st.session_state.GOOGLE_API_KEY = None
            st.rerun()
    
    # 应用功能说明
    st.info(
        "此工具使用先进的计算机视觉和放射学专业知识，"
        "为医疗影像数据提供 AI 驱动的分析服务。"
    )
    
    # 免责声明
    st.warning(
        "⚠️ 免责声明: 此工具仅供教育和信息参考目的。"
        "所有分析结果都应由合格的医疗专业人员审查。"
        "请勿仅基于此分析结果做出医疗决策。"
    )

# ========================= AI 代理初始化 =========================
# 创建医疗影像分析智能代理
# 只有在API密钥配置完成后才初始化代理
medical_agent = Agent(
    model=Gemini(
        id="gemini-2.0-flash",  # 使用最新的 Gemini 2.0 Flash 模型
        api_key=st.session_state.GOOGLE_API_KEY
    ),
    tools=[DuckDuckGoTools()],  # 集成 DuckDuckGo 搜索工具用于文献检索
    markdown=True  # 启用 Markdown 格式输出
) if st.session_state.GOOGLE_API_KEY else None

# 如果代理未初始化，提示用户配置API密钥
if not medical_agent:
    st.warning("请在侧边栏配置您的 API 密钥以继续使用")

# ========================= 医疗分析提示词 =========================
# 定义详细的医疗影像分析提示词
# 这个提示词指导 AI 模型如何进行专业的医疗影像分析
query = """
您是一位具有丰富放射学和诊断影像学知识的医疗影像专家。请分析患者的医疗图像，并按以下结构组织您的回答：

### 1. 影像类型和区域
- 指定成像模式（X光/MRI/CT/超声波等）
- 识别患者的解剖区域和体位
- 评论图像质量和技术充分性

### 2. 关键发现
- 系统性地列出主要观察结果
- 记录患者影像中的任何异常，并提供精确描述
- 包括相关的测量值和密度
- 描述位置、大小、形状和特征
- 评级严重程度：正常/轻度/中度/重度

### 3. 诊断评估
- 提供主要诊断及可信度水平
- 按可能性顺序列出鉴别诊断
- 用患者影像中观察到的证据支持每个诊断
- 注明任何关键或紧急发现

### 4. 患者友好解释
- 用患者能理解的简单、清晰的语言解释发现
- 避免医学术语或提供清晰的定义
- 如有帮助，包括视觉类比
- 回应与这些发现相关的常见患者关切

### 5. 研究背景
重要提示：使用 DuckDuckGo 搜索工具：
- 查找关于类似病例的最新医学文献
- 搜索标准治疗方案
- 提供相关医学链接列表
- 研究任何相关的技术进展
- 包括 2-3 个关键参考文献来支持您的分析

请使用清晰的 markdown 标题和项目符号格式化您的回答。要简洁而全面。
"""

# ========================= 主界面布局 =========================
st.title("🏥 医疗影像诊断智能代理")
st.write("上传医疗图像进行专业分析")

# 创建容器组织界面布局，提高用户体验
upload_container = st.container()    # 图像上传区域
image_container = st.container()     # 图像显示区域
analysis_container = st.container()  # 分析结果区域

# ========================= 图像上传模块 =========================
with upload_container:
    # 文件上传组件，支持多种医疗影像格式
    uploaded_file = st.file_uploader(
        "上传医疗图像",
        type=["jpg", "jpeg", "png", "dicom"],  # 支持的文件格式
        help="支持的格式：JPG、JPEG、PNG、DICOM"
    )

# ========================= 图像处理和显示模块 =========================
if uploaded_file is not None:
    with image_container:
        # 使用三列布局居中显示图像
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            # 图像预处理：加载、调整大小和优化显示
            image = PILImage.open(uploaded_file)
            width, height = image.size
            aspect_ratio = width / height  # 保持宽高比
            
            # 标准化图像尺寸以优化显示和处理速度
            new_width = 500
            new_height = int(new_width / aspect_ratio)
            resized_image = image.resize((new_width, new_height))
            
            # 在界面中显示调整后的图像
            st.image(
                resized_image,
                caption="已上传的医疗图像",
                use_container_width=True
            )
            
            # 分析按钮：触发AI分析流程
            analyze_button = st.button(
                "🔍 分析图像",
                type="primary",
                use_container_width=True
            )
    
    # ========================= AI 分析处理模块 =========================
    with analysis_container:
        if analyze_button:
            # 显示分析进度指示器
            with st.spinner("🔄 正在分析图像... 请稍候。"):
                try:
                    # 临时保存调整后的图像以供AI分析
                    temp_path = "temp_resized_image.png"
                    resized_image.save(temp_path)
                    
                    # 创建 Agno 图像对象，用于AI模型处理
                    agno_image = AgnoImage(filepath=temp_path)
                    
                    # 调用AI代理进行医疗影像分析
                    # 传入专业的分析提示词和图像数据
                    response = medical_agent.run(query, images=[agno_image])
                    
                    # ========================= 结果展示模块 =========================
                    st.markdown("### 📋 分析结果")
                    st.markdown("---")
                    # 显示AI生成的结构化分析报告
                    st.markdown(response.content)
                    st.markdown("---")
                    
                    # 添加专业免责声明
                    st.caption(
                        "注意：此分析由 AI 生成，应由合格的医疗专业人员审查。"
                    )
                    
                    # 清理临时文件
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                        
                except Exception as e:
                    # 错误处理：显示用户友好的错误信息
                    st.error(f"分析过程中出现错误：{e}")
                    # 确保清理临时文件
                    if os.path.exists("temp_resized_image.png"):
                        os.remove("temp_resized_image.png")
else:
    # 默认提示信息：引导用户上传图像
    st.info("👆 请上传医疗图像开始分析")

# ========================= 应用程序结束 =========================
# 注意：Streamlit 应用会自动处理会话管理和资源清理
