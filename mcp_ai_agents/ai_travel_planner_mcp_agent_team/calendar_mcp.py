#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件名: calendar_mcp.py
目的: Google Calendar MCP 服务器实现
作用: 
    1. 实现 MCP (Model Context Protocol) 服务器，提供 Google Calendar API 集成
    2. 为 AI 智能体提供日历事件创建、管理和提醒功能
    3. 处理 OAuth 2.0 身份验证和 Google Calendar API 调用
    4. 支持时区管理、事件详情配置和提醒设置

主要架构:
    - 协议层: 基于 FastMCP 框架实现 MCP 协议
    - 认证层: Google OAuth 2.0 刷新令牌认证
    - API 层: Google Calendar API v3 集成
    - 工具层: 为 AI 智能体提供日历操作工具

技术栈:
    - MCP 框架: FastMCP
    - 认证: Google OAuth 2.0
    - API: Google Calendar API v3
    - 配置: python-dotenv 环境变量管理
"""

import os          # 操作系统接口
import json        # JSON 数据处理
import sys         # 系统相关参数和函数
import logging     # 日志记录

# 环境变量和配置管理
from dotenv import load_dotenv

# Google API 客户端库
from google.oauth2.credentials import Credentials      # OAuth 2.0 凭证
from googleapiclient.discovery import build           # Google API 客户端构建器

# MCP 服务器框架
from mcp.server.fastmcp import FastMCP

# 加载环境变量配置
load_dotenv()

# 配置日志记录系统
logging.basicConfig(
  level=logging.DEBUG,                                 # 设置日志级别为 DEBUG
  format='DEBUG: %(asctime)s - %(message)s',          # 日志格式：时间戳 + 消息
  stream=sys.stderr                                    # 输出到标准错误流
)
logger = logging.getLogger(__name__)

# 创建 FastMCP 服务器实例
mcp = FastMCP(
    "Google Calendar MCP",                             # 服务器名称
    dependencies=[                                     # 依赖包列表
        "python-dotenv", 
        "google-api-python-client", 
        "google-auth", 
        "google-auth-oauthlib"
    ]
)

# 从环境变量获取 Google OAuth 配置
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REFRESH_TOKEN = os.getenv("GOOGLE_REFRESH_TOKEN")

# 验证必要的环境变量是否存在
if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET or not GOOGLE_REFRESH_TOKEN:
  logger.error("错误：需要设置 GOOGLE_CLIENT_ID、GOOGLE_CLIENT_SECRET 和 GOOGLE_REFRESH_TOKEN 环境变量")
  sys.exit(1)

@mcp.tool()
async def create_event(
  summary: str,           # 事件标题
  start_time: str,        # 开始时间（ISO 格式）
  end_time: str,          # 结束时间（ISO 格式）
  description: str = None,  # 事件描述（可选）
  location: str = None,     # 事件地点（可选）
  attendees: list = None,   # 参与者邮箱列表（可选）
  reminders: dict = None    # 提醒设置（可选）
) -> str:
  """
  创建带有指定详细信息的日历事件
  
  Args:
      summary: 事件标题
      start_time: 开始时间（ISO 格式，如：2024-04-20T10:00:00）
      end_time: 结束时间（ISO 格式，如：2024-04-20T12:00:00）
      description: 事件描述（可选）
      location: 事件地点（可选）
      attendees: 参与者邮箱地址列表（可选）
      reminders: 事件提醒设置（可选）
  
  Returns:
      String: 包含事件创建确认和链接的字符串
      
  Raises:
      Exception: 当事件创建失败时抛出异常
  """
  logger.debug(f'正在创建日历事件，参数：{locals()}')
  
  try:
    logger.debug('创建 OAuth2 客户端')
    
    # 创建 Google OAuth2 凭证对象
    creds = Credentials(
      None,                                            # 访问令牌（使用刷新令牌时可为 None）
      refresh_token=GOOGLE_REFRESH_TOKEN,              # 刷新令牌
      token_uri="https://oauth2.googleapis.com/token", # 令牌端点 URI
      client_id=GOOGLE_CLIENT_ID,                      # 客户端 ID
      client_secret=GOOGLE_CLIENT_SECRET               # 客户端密钥
    )
    logger.debug('OAuth2 客户端创建成功')
    
    logger.debug('创建日历服务客户端')
    # 构建 Google Calendar API 服务客户端
    calendar_service = build('calendar', 'v3', credentials=creds)
    logger.debug('日历服务客户端创建成功')
    
    # 构建基础事件对象
    event = {
      'summary': summary,                              # 事件标题
      'start': {
        'dateTime': start_time,                        # 开始时间
        'timeZone': 'Asia/Seoul'                       # 时区设置（可根据需要调整）
      },
      'end': {
        'dateTime': end_time,                          # 结束时间
        'timeZone': 'Asia/Seoul'                       # 时区设置（可根据需要调整）
      }
    }
    
    # 添加可选的事件描述
    if description:
      event['description'] = description
    
    # 添加可选的事件地点
    if location:
      event['location'] = location
      logger.debug(f'已添加地点：{location}')
    
    # 添加可选的参与者
    if attendees:
      event['attendees'] = [{'email': email} for email in attendees]
      logger.debug(f'已添加参与者：{event["attendees"]}')
    
    # 配置事件提醒设置
    if reminders:
      event['reminders'] = reminders
      logger.debug(f'已设置自定义提醒：{json.dumps(reminders)}')
    else:
      # 使用默认提醒设置：事件前 10 分钟弹窗提醒
      event['reminders'] = {
        'useDefault': False,                           # 不使用默认提醒
        'overrides': [
          {'method': 'popup', 'minutes': 10}           # 弹窗提醒，提前 10 分钟
        ]
      }
      logger.debug(f'已设置默认提醒：{json.dumps(event["reminders"])}')
    
    logger.debug('尝试插入事件到日历')
    # 调用 Google Calendar API 创建事件
    response = calendar_service.events().insert(
        calendarId='primary',                          # 使用主日历
        body=event                                     # 事件详情
    ).execute()
    logger.debug(f'事件插入响应：{json.dumps(response)}')
    
    # 返回创建成功的确认信息和事件链接
    return f"事件创建成功：{response.get('htmlLink', '无可用链接')}"
    
  except Exception as error:
    # 详细的错误日志记录
    logger.debug(f'发生错误：')
    logger.debug(f'错误类型：{type(error).__name__}')
    logger.debug(f'错误信息：{str(error)}')
    
    # 记录完整的错误堆栈跟踪
    import traceback
    logger.debug(f'错误堆栈跟踪：{traceback.format_exc()}')
    
    # 抛出包含错误信息的异常
    raise Exception(f"创建事件失败：{str(error)}")

def main():
  """
  运行 MCP 日历服务器
  
  启动 FastMCP 服务器，监听来自 MCP 客户端的请求。
  服务器将持续运行，直到收到中断信号或发生致命错误。
  """
  try:
    logger.info("启动 Google Calendar MCP 服务器...")
    mcp.run()  # 启动 MCP 服务器
  except KeyboardInterrupt:
    logger.info("服务器被用户停止")
  except Exception as e:
    logger.error(f"服务器运行时发生致命错误：{e}")
    sys.exit(1)

# 脚本入口点
if __name__ == "__main__":
  main()