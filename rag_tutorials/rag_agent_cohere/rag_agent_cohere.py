"""
RAG Agent with Cohere 智能检索增强生成系统

目的：
    构建一个基于 Cohere Command-r7b-12-2024 模型的智能文档问答系统，
    用户可以上传 PDF 文档并进行智能问答，当文档中找不到答案时自动进行网络搜索。

作用：
    1. PDF 文档解析和向量化存储
    2. 基于相似度的智能文档检索
    3. 使用 RAG 技术生成准确答案
    4. 当文档无法回答时，智能回退到网络搜索
    5. 提供友好的 Web 交互界面

主要架构：
    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
    │   用户界面层    │────│    逻辑处理层    │────│   数据存储层    │
    │   (Streamlit)   │    │   (LangChain)   │    │   (Qdrant)      │
    └─────────────────┘    └─────────────────┘    └─────────────────┘
           │                        │                        │
           │                        │                        │
    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
    │   文档处理      │    │   RAG 检索      │    │   向量数据库    │
    │   (PyPDF)       │    │   (Retrieval)   │    │   (Vector DB)   │
    └─────────────────┘    └─────────────────┘    └─────────────────┘
           │                        │                        │
           │                        │                        │
    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
    │   网络搜索      │    │   智能体编排    │    │   模型服务      │
    │  (DuckDuckGo)   │    │  (LangGraph)    │    │   (Cohere)      │
    └─────────────────┘    └─────────────────┘    └─────────────────┘

技术栈：
    - 前端：Streamlit (Web 应用框架)
    - 向量数据库：Qdrant Cloud (向量存储与相似度搜索)
    - 语言模型：Cohere Command-r7b-12-2024 (对话生成)
    - 嵌入模型：Cohere embed-english-v3.0 (文本向量化)
    - RAG 框架：LangChain (检索增强生成)
    - 智能体编排：LangGraph (复杂任务流程管理)
    - 文档处理：PyPDFLoader (PDF 解析)
    - 网络搜索：DuckDuckGo Search (外部信息补充)

作者：AI-BOX 团队
版本：1.0
创建时间：2024年
"""

import os
import streamlit as st
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_cohere import CohereEmbeddings, ChatCohere
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain
from langchain import hub
import tempfile
from langgraph.prebuilt import create_react_agent
from langchain_community.tools import DuckDuckGoSearchRun
from typing import TypedDict, List
from langchain_core.language_models import BaseLanguageModel
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from time import sleep
from tenacity import retry, wait_exponential, stop_after_attempt


def init_session_state():
    """
    初始化 Streamlit 会话状态
    
    功能：
        - 设置 API 密钥提交状态
        - 初始化聊天历史记录
        - 初始化向量存储对象
        - 初始化 Qdrant 连接参数
    
    返回：
        无返回值，直接修改 st.session_state
    """
    if 'api_keys_submitted' not in st.session_state:
        st.session_state.api_keys_submitted = False
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'vectorstore' not in st.session_state:
        st.session_state.vectorstore = None
    if 'qdrant_api_key' not in st.session_state:
        st.session_state.qdrant_api_key = ""
    if 'qdrant_url' not in st.session_state:
        st.session_state.qdrant_url = ""

def sidebar_api_form():
    """
    创建侧边栏 API 凭据输入表单
    
    功能：
        - 提供 Cohere API 密钥输入框
        - 提供 Qdrant API 密钥和 URL 输入框
        - 验证 Qdrant 连接有效性
        - 保存验证通过的凭据到会话状态
    
    返回：
        bool: True 表示凭据已验证，False 表示需要输入凭据
    """
    with st.sidebar:
        st.header("API Credentials")
        
        # 如果凭据已提交，显示成功状态和重置选项
        if st.session_state.api_keys_submitted:
            st.success("API credentials verified")
            if st.button("Reset Credentials"):
                st.session_state.clear()
                st.rerun()
            return True
        
        # 创建凭据输入表单
        with st.form("api_credentials"):
            cohere_key = st.text_input("Cohere API Key", type="password")
            qdrant_key = st.text_input("Qdrant API Key", type="password", help="Enter your Qdrant API key")
            qdrant_url = st.text_input("Qdrant URL", 
                                     placeholder="https://xyz-example.eu-central.aws.cloud.qdrant.io:6333",
                                     help="Enter your Qdrant instance URL")
            
            if st.form_submit_button("Submit Credentials"):
                try:
                    # 验证 Qdrant 连接
                    client = QdrantClient(url=qdrant_url, api_key=qdrant_key, timeout=60)
                    client.get_collections()
                    
                    # 保存验证通过的凭据
                    st.session_state.cohere_api_key = cohere_key
                    st.session_state.qdrant_api_key = qdrant_key
                    st.session_state.qdrant_url = qdrant_url
                    st.session_state.api_keys_submitted = True
                    
                    st.success("Credentials verified!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Qdrant connection failed: {str(e)}")
        return False

def init_qdrant() -> QdrantClient:
    """
    初始化 Qdrant 客户端连接
    
    功能：
        - 使用会话状态中的凭据创建 Qdrant 客户端
        - 设置合适的超时时间
        - 验证必要参数是否存在
    
    返回：
        QdrantClient: 已配置的 Qdrant 客户端实例
        
    异常：
        ValueError: 当 API 密钥或 URL 缺失时抛出
    """
    if not st.session_state.get("qdrant_api_key"):
        raise ValueError("Qdrant API key not provided")
    if not st.session_state.get("qdrant_url"):
        raise ValueError("Qdrant URL not provided")
    
    return QdrantClient(url=st.session_state.qdrant_url,
                       api_key=st.session_state.qdrant_api_key,
                       timeout=60)

# 初始化会话状态
init_session_state()

# 检查 API 凭据，如果未提交则停止执行
if not sidebar_api_form():
    st.info("Please enter your API credentials in the sidebar to continue.")
    st.stop()

# 初始化 Cohere 嵌入模型
# 使用 embed-english-v3.0 模型进行文本向量化
embedding = CohereEmbeddings(model="embed-english-v3.0",
                            cohere_api_key=st.session_state.cohere_api_key)

# 初始化 Cohere 聊天模型
# 使用 Command-r7b-12-2024 模型进行对话生成
chat_model = ChatCohere(model="command-r7b-12-2024",
                       temperature=0.1,  # 较低的温度保证答案的一致性
                       max_tokens=512,   # 限制单次回答的最大长度
                       verbose=True,     # 启用详细日志
                       cohere_api_key=st.session_state.cohere_api_key)

# 初始化 Qdrant 客户端
client = init_qdrant()

def process_document(file):
    """
    处理上传的 PDF 文档
    
    功能：
        - 将上传的文件保存为临时文件
        - 使用 PyPDFLoader 解析 PDF 内容
        - 使用 RecursiveCharacterTextSplitter 进行文本分块
        - 清理临时文件
    
    参数：
        file: Streamlit 上传的文件对象
    
    返回：
        list: 分块后的文档列表，每个元素包含文本内容和元数据
    """
    try:
        # 创建临时文件保存上传的 PDF
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(file.getvalue())
            tmp_path = tmp_file.name
            
        # 使用 LangChain 的 PDF 加载器解析文档
        loader = PyPDFLoader(tmp_path)
        documents = loader.load()
        
        # 文本分割器配置
        # chunk_size=1000: 每个文本块最大长度
        # chunk_overlap=200: 相邻文本块的重叠长度，保证上下文连续性
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        texts = text_splitter.split_documents(documents)
        
        # 清理临时文件
        os.unlink(tmp_path)
        
        return texts
    except Exception as e:
        st.error(f"Error processing document: {e}")
        return []

# Qdrant 集合名称常量
COLLECTION_NAME = "cohere_rag"

def create_vector_stores(texts):
    """
    创建并填充向量存储
    
    功能：
        - 在 Qdrant 中创建新的集合（如果不存在）
        - 配置向量维度和距离度量方式
        - 将文档文本转换为向量并存储
        - 提供用户反馈和错误处理
    
    参数：
        texts (list): 分块后的文档列表
    
    返回：
        QdrantVectorStore: 配置好的向量存储对象，失败时返回 None
    """
    try:
        try:
            # 创建 Qdrant 集合
            # size=1024: Cohere embed-english-v3.0 模型的向量维度
            # distance=COSINE: 使用余弦相似度进行向量比较
            client.create_collection(collection_name=COLLECTION_NAME,
                                   vectors_config=VectorParams(size=1024,
                                                            distance=Distance.COSINE))
            st.success(f"Created new collection: {COLLECTION_NAME}")
        except Exception as e:
            # 如果集合已存在，忽略错误
            if "already exists" not in str(e).lower():
                raise e
        
        # 创建 LangChain 向量存储包装器
        vector_store = QdrantVectorStore(client=client,
                                       collection_name=COLLECTION_NAME,
                                       embedding=embedding)
        
        # 批量添加文档到向量存储
        with st.spinner('Storing documents in Qdrant...'):
            vector_store.add_documents(texts)
            st.success("Documents successfully stored in Qdrant!")
        
        return vector_store
        
    except Exception as e:
        st.error(f"Error in vector store creation: {str(e)}")
        return None

# 定义智能体状态的类型架构
class AgentState(TypedDict):
    """
    智能体状态的类型定义
    
    属性：
        messages: 对话消息列表，包含用户消息、AI 消息和系统消息
        is_last_step: 标识是否为最后一步的布尔值
    """
    messages: List[HumanMessage | AIMessage | SystemMessage]
    is_last_step: bool

class RateLimitedDuckDuckGo(DuckDuckGoSearchRun):
    """
    带速率限制的 DuckDuckGo 搜索工具
    
    功能：
        - 继承自 DuckDuckGoSearchRun
        - 添加重试机制和速率限制处理
        - 自动处理搜索 API 的速率限制错误
    """
    @retry(wait=wait_exponential(multiplier=1, min=4, max=10),
           stop=stop_after_attempt(3))
    def run(self, query: str) -> str:
        """
        执行带速率限制的搜索
        
        参数：
            query (str): 搜索查询字符串
        
        返回：
            str: 搜索结果
        """
        try:
            sleep(2)  # 在请求之间添加延迟
            return super().run(query)
        except Exception as e:
            if "Ratelimit" in str(e):
                sleep(5)  # 遇到速率限制时等待更长时间
                return super().run(query)
            raise e

def create_fallback_agent(chat_model: BaseLanguageModel):
    """
    创建用于网络研究的 LangGraph 智能体
    
    功能：
        - 创建网络搜索工具
        - 配置 ReAct 智能体进行复杂推理
        - 提供搜索失败时的优雅降级
    
    参数：
        chat_model: 用于智能体推理的语言模型
    
    返回：
        LangGraph Agent: 配置好的智能体实例
    """
    
    def web_research(query: str) -> str:
        """
        网络搜索工具函数
        
        参数：
            query (str): 搜索查询
        
        返回：
            str: 格式化的搜索结果
        """
        try:
            # 创建搜索工具，限制结果数量
            search = DuckDuckGoSearchRun(num_results=5)
            results = search.run(query)
            return results
        except Exception as e:
            return f"Search failed: {str(e)}. Providing answer based on general knowledge."

    # 定义智能体可用的工具列表
    tools = [web_research]
    
    # 创建 ReAct 智能体
    # ReAct = Reasoning + Acting，能够进行推理并执行操作
    agent = create_react_agent(model=chat_model,
                             tools=tools,
                             debug=False)
    
    return agent

def process_query(vectorstore, query) -> tuple[str, list]:
    """
    处理用户查询，支持 RAG 检索和网络搜索回退
    
    功能：
        - 使用向量相似度搜索检索相关文档
        - 如果找到相关文档，使用 RAG 生成答案
        - 如果未找到相关文档，自动回退到网络搜索
        - 提供详细的错误处理和用户反馈
    
    参数：
        vectorstore: 向量存储对象
        query (str): 用户查询
    
    返回：
        tuple[str, list]: (答案字符串, 相关文档列表)
    """
    try:
        # 配置检索器
        # similarity_score_threshold: 使用相似度阈值过滤
        # k=10: 最多检索 10 个相关文档
        # score_threshold=0.7: 相似度阈值为 0.7，过滤不相关的文档
        retriever = vectorstore.as_retriever(
            search_type="similarity_score_threshold",
            search_kwargs={
                "k": 10,
                "score_threshold": 0.7
            }
        )

        # 获取相关文档
        relevant_docs = retriever.get_relevant_documents(query)

        if relevant_docs:
            # 如果找到相关文档，使用 RAG 生成答案
            
            # 从 LangChain Hub 获取预定义的 RAG 提示模板
            retrieval_qa_prompt = hub.pull("langchain-ai/retrieval-qa-chat")
            
            # 创建文档合并链，将多个文档合并为上下文
            combine_docs_chain = create_stuff_documents_chain(chat_model, retrieval_qa_prompt)
            
            # 创建检索链，结合检索器和文档合并链
            retrieval_chain = create_retrieval_chain(retriever, combine_docs_chain)
            
            # 执行 RAG 查询
            response = retrieval_chain.invoke({"input": query})
            return response['answer'], relevant_docs
            
        else:
            # 如果未找到相关文档，回退到网络搜索
            st.info("No relevant documents found. Searching web...")
            fallback_agent = create_fallback_agent(chat_model)
            
            with st.spinner('Researching...'):
                # 构造智能体输入
                agent_input = {
                    "messages": [
                        HumanMessage(content=f"""Please thoroughly research the question: '{query}' and provide a detailed and comprehensive response. Make sure to gather the latest information from credible sources. Minimum 400 words.""")
                    ],
                    "is_last_step": False
                }
                
                # 配置智能体执行参数
                config = {"recursion_limit": 100}
                
                try:
                    # 执行智能体研究
                    response = fallback_agent.invoke(agent_input, config=config)
                    
                    # 提取智能体生成的答案
                    if isinstance(response, dict) and "messages" in response:
                        last_message = response["messages"][-1]
                        answer = last_message.content if hasattr(last_message, 'content') else str(last_message)
                        
                        return f"""Web Search Result:
{answer}
""", []
                    
                except Exception as agent_error:
                    # 智能体失败时的最后回退
                    fallback_response = chat_model.invoke(f"Please provide a general answer to: {query}").content
                    return f"Web search unavailable. General response: {fallback_response}", []

    except Exception as e:
        st.error(f"Error: {str(e)}")
        return "I encountered an error. Please try rephrasing your question.", []

def post_process(answer, sources):
    """
    后处理答案和来源信息
    
    功能：
        - 对过长的答案进行摘要
        - 格式化来源文档信息
        - 提供清晰的信息展示
    
    参数：
        answer (str): 原始答案
        sources (list): 来源文档列表
    
    返回：
        tuple: (处理后的答案, 格式化的来源列表)
    """
    answer = answer.strip()

    # 对超过 500 字符的答案进行摘要
    if len(answer) > 500:
        summary_prompt = f"Summarize the following answer in 2-3 sentences: {answer}"
        summary = chat_model.invoke(summary_prompt).content
        answer = f"{summary}\n\nFull Answer: {answer}"
    
    # 格式化来源信息
    formatted_sources = []
    for i, source in enumerate(sources, 1):
        # 截取前 200 个字符作为预览
        formatted_source = f"{i}. {source.page_content[:200]}..."
        formatted_sources.append(formatted_source)
    return answer, formatted_sources

# ================================
# Streamlit 用户界面部分
# ================================

st.title("RAG Agent with Cohere ⌘R")

# 文件上传组件
uploaded_file = st.file_uploader("Choose a PDF or Image File", type=["pdf", "jpg", "jpeg"])

# 处理上传的文件
if uploaded_file is not None and 'processed_file' not in st.session_state:
    with st.spinner('Processing file... This may take a while for images.'):
        # 处理文档并创建向量存储
        texts = process_document(uploaded_file)
        vectorstore = create_vector_stores(texts)
        if vectorstore:
            st.session_state.vectorstore = vectorstore
            st.session_state.processed_file = True
            st.success('File uploaded and processed successfully!')
        else:
            st.error('Failed to process file. Please try again.')

# 显示聊天历史
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 处理用户输入
if query := st.chat_input("Ask a question about the document:"):
    # 添加用户消息到历史记录
    st.session_state.chat_history.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    # 生成 AI 回复
    if st.session_state.vectorstore:
        with st.chat_message("assistant"):
            try:
                # 处理查询并获取答案
                answer, sources = process_query(st.session_state.vectorstore, query)
                st.markdown(answer)
                
                # 显示来源信息
                if sources:
                    with st.expander("Sources"):
                        for source in sources:
                            st.markdown(f"- {source.page_content[:200]}...")
                
                # 添加 AI 回复到历史记录
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": answer
                })
                
            except Exception as e:
                st.error(f"Error: {str(e)}")
                st.info("Please try asking your question again.")
    else:
        st.error("Please upload a document first.")

# 侧边栏控制按钮
with st.sidebar:
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        if st.button('Clear Chat History'):
            st.session_state.chat_history = []
            st.rerun()
    with col2:
        if st.button('Clear All Data'):
            try:
                # 清理 Qdrant 中的所有集合
                collections = client.get_collections().collections
                collection_names = [col.name for col in collections]
                
                if COLLECTION_NAME in collection_names:
                    client.delete_collection(COLLECTION_NAME)
                if f"{COLLECTION_NAME}_compressed" in collection_names:
                    client.delete_collection(f"{COLLECTION_NAME}_compressed")
                
                # 重置会话状态
                st.session_state.vectorstore = None
                st.session_state.chat_history = []
                st.success("All data cleared successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"Error clearing data: {str(e)}")
