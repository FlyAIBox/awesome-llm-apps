#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件名: app.py
目的: AI 旅行规划 MCP 智能体团队主应用程序
作用: 
    1. 提供基于 Streamlit 的 Web 界面，让用户输入旅行需求
    2. 集成多个 MCP 服务器（地图、天气、预订、日历）
    3. 协调多个 AI 智能体合作完成旅行规划任务
    4. 管理 API 密钥配置和用户交互

主要架构:
    - 前端: Streamlit 响应式 Web 界面
    - 后端: 基于 Agno 框架的多智能体系统
    - 集成: MCP 协议统一管理外部服务
    - 协作: 四个专业智能体（地图、天气、预订、日历）协同工作
    
技术栈:
    - UI 框架: Streamlit
    - AI 框架: Agno (Agent Framework)
    - 异步处理: AsyncIO
    - 协议: MCP (Model Context Protocol)
    - 模型: OpenAI GPT-4o-mini
"""

import asyncio  # 异步编程支持
import os       # 操作系统接口

# 导入 Agno 框架相关模块
from agno.agent import Agent                    # 智能体基类
from agno.team.team import Team                 # 智能体团队管理
from agno.tools.mcp import MultiMCPTools        # MCP 工具集成
from agno.models.openai import OpenAIChat       # OpenAI 聊天模型

import streamlit as st      # Streamlit Web 应用框架
from datetime import date   # 日期处理

# 注意：移除了 dotenv 导入，因为我们使用侧边栏配置
# from dotenv import load_dotenv
# load_dotenv()

async def run_agent(message: str):
    """
    运行 AI 智能体团队处理旅行规划请求
    
    Args:
        message (str): 用户的旅行规划需求描述
        
    Returns:
        str: 智能体团队生成的旅行计划结果
        
    Raises:
        ValueError: 当缺少必要的 API 密钥时抛出异常
    """
    
    # 从 Streamlit 会话状态获取 API 密钥
    google_maps_key = st.session_state.get('google_maps_key')
    accuweather_key = st.session_state.get('accuweather_key')
    openai_key = st.session_state.get('openai_key')
    google_client_id = st.session_state.get('google_client_id')
    google_client_secret = st.session_state.get('google_client_secret')
    google_refresh_token = st.session_state.get('google_refresh_token')

    # 验证必要的 API 密钥是否存在
    if not google_maps_key:
        raise ValueError("🚨 缺少 Google Maps API 密钥。请在侧边栏中输入。")
    elif not accuweather_key:
        raise ValueError("🚨 缺少 AccuWeather API 密钥。请在侧边栏中输入。")
    elif not openai_key:
        raise ValueError("🚨 缺少 OpenAI API 密钥。请在侧边栏中输入。")
    elif not google_client_id:
        raise ValueError("🚨 缺少 Google 客户端 ID。请在侧边栏中输入。")
    elif not google_client_secret:
        raise ValueError("🚨 缺少 Google 客户端密钥。请在侧边栏中输入。")
    elif not google_refresh_token:
        raise ValueError("🚨 缺少 Google 刷新令牌。请在侧边栏中输入。")

    # 👉 全局设置 OPENAI_API_KEY 环境变量
    os.environ["OPENAI_API_KEY"] = openai_key

    # 构建完整的环境变量字典，包含所有必需的 API 密钥
    env = {
        **os.environ,
        "GOOGLE_MAPS_API_KEY": google_maps_key,
        "ACCUWEATHER_API_KEY": accuweather_key,
        "OPENAI_API_KEY": openai_key,
        "GOOGLE_CLIENT_ID": google_client_id,
        "GOOGLE_CLIENT_SECRET": google_client_secret,
        "GOOGLE_REFRESH_TOKEN": google_refresh_token
    }

    # 使用 MultiMCPTools 异步上下文管理器集成多个 MCP 服务器
    async with MultiMCPTools(
        [
            "npx -y @openbnb/mcp-server-airbnb --ignore-robots-txt",  # ✅ Airbnb MCP 服务器
            "npx -y @modelcontextprotocol/server-google-maps",        # ✅ Google Maps MCP 服务器
            "uvx --from git+https://github.com/adhikasp/mcp-weather.git mcp-weather",  # ✅ 天气 MCP 服务器
            "./calendar_mcp.py"  # ✅ 日历 MCP 服务器（本地实现）
        ],
        env=env,  # 传递环境变量
    ) as mcp_tools:
        
        # 定义专业化智能体，每个智能体负责特定领域的任务
        
        # 地图智能体：负责路线规划、位置服务和导航
        maps_agent = Agent(
            tools=[mcp_tools],
            model=OpenAIChat(id="gpt-4o-mini", api_key=openai_key),
            name="Maps Agent",
            goal="""作为地图智能体，您的职责包括：
            1. 寻找地点之间的最优路线
            2. 识别目的地附近的兴趣点
            3. 计算旅行时间和距离
            4. 建议交通选择方案
            5. 查找附近的便利设施和服务
            6. 提供基于位置的推荐
            
            始终考虑：
            - 交通状况和高峰时段
            - 备选路线和交通方式
            - 可达性和便利性
            - 安全性和照明良好的区域
            - 与其他计划活动的邻近性"""
        )

        # 天气智能体：负责天气预报和相关建议
        weather_agent = Agent(
            tools=[mcp_tools],
            name="Weather Agent",
            model=OpenAIChat(id="gpt-4o-mini", api_key=openai_key),
            goal="""作为天气智能体，您的职责包括：
            1. 为目的地提供详细的天气预报
            2. 提醒严重的天气条件
            3. 建议适合天气的活动
            4. 基于天气条件推荐最佳旅行时间
            5. 提供季节性旅行建议
            
            始终考虑：
            - 温度范围和舒适度
            - 降水概率
            - 风力条件
            - 紫外线指数和防晒保护
            - 季节性变化
            - 天气警报和预警"""
        )

        # 预订智能体：负责住宿预订和价格比较
        booking_agent = Agent(
            tools=[mcp_tools],
            name="Booking Agent",
            model=OpenAIChat(id="gpt-4o-mini", api_key=openai_key),
            goal="""作为预订智能体，您的职责包括：
            1. 在预算范围内在 Airbnb 上寻找住宿
            2. 跨平台比较价格
            3. 检查特定日期的可用性
            4. 验证设施和政策
            5. 在适用时寻找最后一刻的优惠
            
            始终考虑：
            - 位置便利性
            - 价格竞争力
            - 取消政策
            - 客人评价和评分
            - 符合偏好的设施
            - 特殊要求或无障碍需求"""
        )

        # 日历智能体：负责行程安排和日程管理
        calendar_agent = Agent(
            tools=[mcp_tools],
            name="Calendar Agent",
            model=OpenAIChat(id="gpt-4o-mini", api_key=openai_key),
            goal="""作为日历智能体，您的职责包括：
            1. 创建详细的旅行行程
            2. 为预订和入住设置提醒
            3. 安排活动和预约
            4. 为预订截止日期、入住和其他重要事件添加提醒
            5. 与其他团队成员的日程协调
            
            始终考虑：
            - 时区差异
            - 活动之间的旅行时间
            - 意外延误的缓冲时间
            - 重要截止日期和入住时间
            - 与其他团队成员的同步"""
        )

        # 创建智能体团队，协调多个智能体合作
        team = Team(
            members=[maps_agent, weather_agent, booking_agent, calendar_agent],
            name="Travel Planning Team",
            markdown=True,          # 启用 Markdown 格式输出
            show_tool_calls=True,   # 显示工具调用过程
            instructions="""作为旅行规划团队，协调创建全面的旅行计划：
            1. 在智能体之间共享信息以确保一致性
            2. 考虑旅行各个方面之间的依赖关系
            3. 优先考虑用户偏好和约束
            4. 当主要选择不可用时提供备选方案
            5. 在计划活动和自由时间之间保持平衡
            6. 考虑当地事件和季节性因素
            7. 确保所有推荐都符合用户的预算
            8. 提供旅行的详细分解，包括预订、路线、天气和计划活动
            9. 在用户日历中添加旅行开始日期"""
        )

        # 运行智能体团队处理用户请求
        result = await team.arun(message)
        # 获取最后一条消息的内容作为输出
        output = result.messages[-1].content
        return output  
    
# -------------------- Streamlit 应用程序界面 --------------------
    
# 配置页面基本信息
st.set_page_config(
    page_title="AI Travel Planner",  # 页面标题
    page_icon="✈️",                  # 页面图标
    layout="wide"                    # 宽布局
)

# 添加侧边栏用于 API 密钥配置
with st.sidebar:
    st.header("🔑 API 密钥配置")
    st.markdown("请输入您的 API 密钥以使用旅行规划器。")
    
    # 初始化会话状态中的 API 密钥（如果不存在）
    if 'google_maps_key' not in st.session_state:
        st.session_state.google_maps_key = ""
    if 'accuweather_key' not in st.session_state:
        st.session_state.accuweather_key = ""
    if 'openai_key' not in st.session_state:
        st.session_state.openai_key = ""
    if 'google_client_id' not in st.session_state:
        st.session_state.google_client_id = ""
    if 'google_client_secret' not in st.session_state:
        st.session_state.google_client_secret = ""
    if 'google_refresh_token' not in st.session_state:
        st.session_state.google_refresh_token = ""

    # API 密钥输入字段
    st.session_state.google_maps_key = st.text_input(
        "Google Maps API 密钥",
        value=st.session_state.google_maps_key,
        type="password"  # 密码类型输入，隐藏内容
    )
    st.session_state.accuweather_key = st.text_input(
        "AccuWeather API 密钥",
        value=st.session_state.accuweather_key,
        type="password"
    )
    st.session_state.openai_key = st.text_input(
        "OpenAI API 密钥",
        value=st.session_state.openai_key,
        type="password"
    )
    st.session_state.google_client_id = st.text_input(
        "Google 客户端 ID",
        value=st.session_state.google_client_id,
        type="password"
    )
    st.session_state.google_client_secret = st.text_input(
        "Google 客户端密钥",
        value=st.session_state.google_client_secret,
        type="password"
    )
    st.session_state.google_refresh_token = st.text_input(
        "Google 刷新令牌",
        value=st.session_state.google_refresh_token,
        type="password"
    )

    # 检查是否所有 API 密钥都已填写
    all_keys_filled = all([
        st.session_state.google_maps_key,
        st.session_state.accuweather_key,
        st.session_state.openai_key,
        st.session_state.google_client_id,
        st.session_state.google_client_secret,
        st.session_state.google_refresh_token
    ])

    # 显示配置状态
    if not all_keys_filled:
        st.warning("⚠️ 请填写所有 API 密钥以使用旅行规划器。")
    else:
        st.success("✅ 所有 API 密钥已配置完成！")

# 主页面标题和描述
st.title("✈️ AI 旅行规划器")
st.markdown("""
这个 AI 驱动的旅行规划器帮助您创建个性化的旅行行程，使用：
- 🗺️ 地图和导航服务
- 🌤️ 天气预报
- 🏨 住宿预订
- 📅 日历管理
""")

# 创建两列布局用于输入
col1, col2 = st.columns(2)

with col1:
    # 出发地和目的地输入
    source = st.text_input("出发地", placeholder="输入您的出发城市")
    destination = st.text_input("目的地", placeholder="输入您的目的地城市")
    
    # 旅行日期选择
    travel_dates = st.date_input(
        "旅行日期",
        [date.today(), date.today()],  # 默认值为今天
        min_value=date.today(),        # 最小值为今天
        help="选择您的旅行日期"
    )

with col2:
    # 预算输入
    budget = st.number_input(
        "预算（美元）",
        min_value=0,
        max_value=10000,
        step=100,
        help="输入您的旅行总预算"
    )
    
    # 旅行偏好多选
    travel_preferences = st.multiselect(
        "旅行偏好",
        ["冒险", "放松", "观光", "文化体验", 
         "海滩", "山区", "奢华", "经济实惠", "美食",
         "购物", "夜生活", "家庭友好"],
        help="选择您的旅行偏好"
    )

# 附加偏好设置
st.subheader("附加偏好")
col3, col4 = st.columns(2)

with col3:
    # 住宿类型选择
    accommodation_type = st.selectbox(
        "首选住宿类型",
        ["任意", "酒店", "青年旅社", "公寓", "度假村"],
        help="选择您首选的住宿类型"
    )
    
    # 交通方式多选
    transportation_mode = st.multiselect(
        "首选交通方式",
        ["火车", "公交", "飞机", "租车"],
        help="选择您首选的交通方式"
    )

with col4:
    # 饮食限制多选
    dietary_restrictions = st.multiselect(
        "饮食限制",
        ["无", "素食", "纯素", "无麸质", "清真", "犹太洁食"],
        help="选择任何饮食限制"
    )

# 提交按钮
if st.button("规划我的旅行", type="primary", disabled=not all_keys_filled):
    # 验证必要输入
    if not source or not destination:
        st.error("请输入出发地和目的地城市。")
    elif not travel_preferences:
        st.warning("考虑选择一些旅行偏好以获得更好的推荐。")
    else:
        # 创建加载动画
        with st.spinner("🤖 AI 智能体正在规划您的完美旅行..."):
            try:
                # 为智能体构建消息
                message = f"""
                使用以下详细信息规划旅行：
                - 从：{source}
                - 到：{destination}
                - 日期：{travel_dates[0]} 到 {travel_dates[1]}
                - 预算（美元）：${budget}
                - 偏好：{', '.join(travel_preferences)}
                - 住宿：{accommodation_type}
                - 交通：{', '.join(transportation_mode)}
                - 饮食限制：{', '.join(dietary_restrictions)}
                
                请提供全面的旅行计划，包括：
                1. 推荐的住宿
                2. 每日行程和活动
                3. 交通选择
                4. 预期的每日天气
                5. 预估旅行费用
                6. 将出发日期添加到日历
                """
                
                # 运行智能体
                response = asyncio.run(run_agent(message))
                
                # 显示响应结果
                st.success("✅ 您的旅行计划已准备就绪！")
                st.markdown(response)
                
            except Exception as e:
                # 错误处理
                st.error(f"规划您的旅行时发生错误：{str(e)}")
                st.info("请重试，或如果问题持续存在，请联系支持。")

# 添加页脚
st.markdown("---")
st.markdown("""
<div style='text-align: center'>
    <p>由 AI 旅行规划智能体提供支持</p>
    <p>您的个人旅行助手，创造难忘的体验</p>
</div>
""", unsafe_allow_html=True)