# 🔧 配置说明文档

## 环境变量配置

本项目需要配置多个 API 密钥才能正常运行。请按照以下步骤进行配置：

### 1. 创建环境变量文件

在项目根目录创建 `.env` 文件，并添加以下配置：

```bash
# ==================== Google API 配置 ====================
# Google Maps API 密钥
GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here

# Google OAuth 2.0 客户端配置
GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here

# Google 刷新令牌
GOOGLE_REFRESH_TOKEN=your_google_refresh_token_here

# ==================== 天气 API 配置 ====================
# AccuWeather API 密钥
ACCUWEATHER_API_KEY=your_accuweather_api_key_here

# ==================== AI 模型配置 ====================
# OpenAI API 密钥
OPENAI_API_KEY=your_openai_api_key_here
```

### 2. API 密钥获取指南

#### 🗺️ Google Maps API 密钥

1. 访问 [Google Cloud Console](https://console.cloud.google.com/)
2. 创建新项目或选择现有项目
3. 启用 Google Maps JavaScript API
4. 创建 API 密钥
5. 限制 API 密钥的使用范围（推荐）

**文档链接**: https://developers.google.com/maps/documentation/javascript/get-api-key

#### 📅 Google Calendar API 配置

1. 在 Google Cloud Console 中启用 Google Calendar API
2. 创建 OAuth 2.0 客户端 ID：
   - 应用类型：Web 应用程序
   - 授权重定向 URI：`http://localhost:8080/callback`（用于本地测试）
3. 下载客户端配置文件
4. 获取刷新令牌：
   ```bash
   # 使用 Google OAuth 2.0 Playground 或自定义脚本获取
   # 需要以下权限范围：
   # https://www.googleapis.com/auth/calendar
   ```

**文档链接**: https://developers.google.com/calendar/api/quickstart/python

#### 🌤️ AccuWeather API 密钥

1. 访问 [AccuWeather Developer Portal](https://developer.accuweather.com/)
2. 注册开发者账户
3. 创建新应用
4. 获取 API 密钥
5. 选择合适的定价计划（免费版本每日限制 50 次请求）

**文档链接**: https://developer.accuweather.com/getting-started

#### 🤖 OpenAI API 密钥

1. 访问 [OpenAI Platform](https://platform.openai.com/)
2. 注册或登录账户
3. 前往 [API Keys](https://platform.openai.com/api-keys) 页面
4. 创建新的 API 密钥
5. 确保账户有足够的余额使用 GPT-4o-mini 模型

**文档链接**: https://platform.openai.com/docs/quickstart

### 3. 配置验证

配置完成后，可以通过以下方式验证：

1. **在应用中验证**：
   - 启动应用：`streamlit run app.py`
   - 在侧边栏输入所有 API 密钥
   - 查看是否显示 "✅ 所有 API 密钥已配置完成！"

2. **单独测试 API**：
   ```bash
   # 测试 Google Maps API
   curl "https://maps.googleapis.com/maps/api/geocode/json?address=1600+Amphitheatre+Parkway,+Mountain+View,+CA&key=YOUR_API_KEY"
   
   # 测试 AccuWeather API
   curl "http://dataservice.accuweather.com/locations/v1/cities/search?apikey=YOUR_API_KEY&q=Beijing"
   ```

### 4. 安全最佳实践

#### 🔒 API 密钥安全

- **不要提交到版本控制**：确保 `.env` 文件在 `.gitignore` 中
- **设置使用限制**：为每个 API 密钥设置适当的使用限制
- **定期轮换**：定期更新 API 密钥
- **监控使用**：定期检查 API 使用情况

#### 🛡️ 访问控制

- **IP 限制**：在可能的情况下限制 API 密钥的访问 IP
- **域名限制**：为 Web API 设置域名限制
- **权限最小化**：只授予必要的权限范围

### 5. 故障排除

#### 常见问题

1. **API 密钥无效**
   - 检查密钥是否正确复制
   - 确认 API 是否已启用
   - 验证账户是否有足够的配额

2. **OAuth 认证失败**
   - 检查客户端 ID 和密钥是否正确
   - 确认刷新令牌是否有效
   - 验证权限范围是否正确

3. **配额超限**
   - 检查 API 使用情况
   - 升级到付费计划
   - 优化 API 调用频率

#### 调试技巧

1. **启用详细日志**：
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

2. **检查网络连接**：
   ```bash
   ping google.com
   curl -I https://api.openai.com/v1/models
   ```

3. **验证环境变量**：
   ```python
   import os
   print("API Keys loaded:", bool(os.getenv("OPENAI_API_KEY")))
   ```

### 6. 成本估算

| 服务 | 免费配额 | 付费价格 | 预估月费用 |
|------|----------|----------|------------|
| Google Maps API | $200/月 | $2-5/1000请求 | $10-30 |
| Google Calendar API | 免费 | 免费 | $0 |
| AccuWeather API | 50请求/天 | $25+/月 | $25+ |
| OpenAI API | - | $0.15/1M tokens | $10-50 |

**总计预估**: $45-105/月（取决于使用量）

### 7. 联系支持

如果遇到配置问题，请：

1. 检查本文档的故障排除部分
2. 查看项目的 GitHub Issues
3. 联系相关 API 提供商的技术支持

---

**注意**: 请确保所有 API 密钥都有效且具有足够的配额，否则应用程序可能无法正常工作。 