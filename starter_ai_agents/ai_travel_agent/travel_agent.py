from textwrap import dedent
from agno.agent import Agent
from agno.tools.serpapi import SerpApiTools
import streamlit as st
from agno.models.openai import OpenAIChat

# 设置 Streamlit 应用界面
st.title("AI Travel Planner ✈️")
st.caption("使用AI旅行规划师规划您的下一次冒险，通过GPT-4o自动研究和规划个性化行程")

# 从用户获取 OpenAI API 密钥
openai_api_key = st.text_input("请输入OpenAI API密钥以访问GPT-4o", type="password")

# 从用户获取 SerpAPI 密钥
serp_api_key = st.text_input("请输入SerpAPI密钥以启用搜索功能", type="password")

# 当用户提供了两个API密钥后，初始化AI智能体
if openai_api_key and serp_api_key:
    # 创建研究员智能体
    # 负责搜索旅行目的地、活动和住宿信息
    researcher = Agent(
        name="Researcher",  # 智能体名称
        role="根据用户偏好搜索旅行目的地、活动和住宿",  # 智能体角色
        model=OpenAIChat(id="gpt-4o", api_key=openai_api_key),  # 使用GPT-4o模型
        description=dedent(
            """\
        您是一位世界级的旅行研究专家。根据用户提供的旅行目的地和旅行天数，
        生成相关的搜索关键词来查找相关的旅行活动和住宿信息。
        然后为每个关键词搜索网络，分析结果，并返回10个最相关的结果。
        """
        ),
        instructions=[
            "根据用户提供的旅行目的地和旅行天数，首先生成3个与目的地和天数相关的搜索关键词。",
            "对每个搜索关键词执行`search_google`并分析结果。",
            "从所有搜索结果中，返回与用户偏好最相关的10个结果。",
            "记住：结果的质量很重要。",
        ],
        tools=[SerpApiTools(api_key=serp_api_key)],  # 配置搜索工具
        add_datetime_to_instructions=True,  # 在指令中添加时间戳
    )
    
    # 创建规划师智能体
    # 负责基于研究结果生成个性化行程计划
    planner = Agent(
        name="Planner",  # 智能体名称
        role="基于用户偏好和研究结果生成行程草案",  # 智能体角色
        model=OpenAIChat(id="gpt-4o", api_key=openai_api_key),  # 使用GPT-4o模型
        description=dedent(
            """\
        您是一位资深的旅行规划师。根据用户提供的旅行目的地、旅行天数和研究结果列表，
        您的目标是生成一个满足用户需求和偏好的行程草案。
        """
        ),
        instructions=[
            "根据用户提供的旅行目的地、旅行天数和研究结果列表，生成一个包含建议活动和住宿的行程草案。",
            "确保行程结构良好、信息丰富且具有吸引力。",
            "确保您提供一个细致且平衡的行程，尽可能引用事实。",
            "记住：行程的质量很重要。",
            "注重清晰度、连贯性和整体质量。",
            "永远不要编造事实或剽窃。始终提供适当的归属。",
        ],
        add_datetime_to_instructions=True,  # 在指令中添加时间戳
    )

    # 用户输入字段：目的地和旅行天数
    destination = st.text_input("您想去哪里？")
    num_days = st.number_input("您想旅行多少天？", min_value=1, max_value=30, value=7)

    # 生成行程按钮
    if st.button("生成行程"):
        # 第一步：进行目的地研究
        with st.spinner("正在研究您的目的地..."):
            # 首先获取研究结果
            research_results = researcher.run(f"研究{destination}，为期{num_days}天的旅行", stream=False)
            
            # 显示研究进度
            st.write("✓ 研究完成")
            
        # 第二步：创建个性化行程
        with st.spinner("正在创建您的个性化行程..."):
            # 将研究结果传递给规划师
            prompt = f"""
            目的地：{destination}
            持续时间：{num_days}天
            研究结果：{research_results.content}
            
            请基于这些研究结果创建一个详细的行程计划。
            """
            response = planner.run(prompt, stream=False)
            # 显示生成的行程
            st.write(response.content)