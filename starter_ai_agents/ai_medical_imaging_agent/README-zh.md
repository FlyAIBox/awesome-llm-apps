# 🩻 医疗影像诊断智能代理

基于 Agno 框架构建的医疗影像诊断智能代理，采用 Gemini 2.0 Flash 模型，提供 AI 辅助的医疗影像分析服务。该代理充当医疗影像诊断专家，能够分析各种类型的医疗图像和视频，提供详细的诊断见解和解释。

## 核心功能

- **全面的图像分析**
  - 影像类型识别（X光、MRI、CT扫描、超声波等）
  - 解剖区域检测
  - 关键发现和观察
  - 潜在异常检测
  - 图像质量评估
  - 研究和参考资料查询

## 运行指南

1. **环境设置**
   ```bash
   # 克隆仓库
   git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
   cd ai_agent_tutorials/ai_medical_imaging_agent

   # 安装依赖
   pip install -r requirements.txt
   ```

2. **配置API密钥**
   - 从 [Google AI Studio](https://aistudio.google.com) 获取 Google API 密钥

3. **启动应用**
   ```bash
   streamlit run ai_medical_imaging.py
   ```

## 分析组件

- **影像类型和区域**
  - 识别成像模式
  - 指定解剖区域

- **关键发现**
  - 系统性观察列表
  - 详细外观描述
  - 异常突出显示

- **诊断评估**
  - 潜在诊断排序
  - 鉴别诊断
  - 严重程度评估

- **患者友好解释**
  - 简化术语
  - 详细的基础原理解释
  - 视觉参考点

## 技术栈

- **前端框架**: Streamlit 1.40.2
- **AI 框架**: Agno (基于 Gemini 2.0 Flash)
- **图像处理**: Pillow 10.0.0
- **搜索工具**: DuckDuckGo Search 6.4.1
- **AI 模型**: Google Generative AI 0.8.3

## 架构设计

```
用户界面 (Streamlit)
    ↓
图像上传与预处理 (Pillow)
    ↓
AI 代理 (Agno + Gemini 2.0 Flash)
    ↓
医疗影像分析引擎
    ↓
外部研究查询 (DuckDuckGo)
    ↓
结构化诊断报告
```

## 使用说明

1. **上传医疗影像**：支持 JPG、JPEG、PNG、DICOM 格式
2. **配置 API 密钥**：在侧边栏输入 Google API 密钥
3. **开始分析**：点击"分析图像"按钮
4. **查看结果**：获得结构化的诊断报告

## 分析流程

1. **影像预处理**：调整图像大小和格式
2. **AI 模型分析**：使用 Gemini 2.0 Flash 进行深度分析
3. **文献检索**：通过 DuckDuckGo 查询相关医学文献
4. **报告生成**：生成包含5个部分的详细报告：
   - 影像类型和区域
   - 关键发现
   - 诊断评估
   - 患者友好解释
   - 研究背景

## 特性

- **实时分析**：快速的医疗影像处理
- **多模态支持**：支持各种医疗影像格式
- **智能诊断**：基于最新AI技术的诊断建议
- **文献支持**：自动检索相关医学文献
- **用户友好**：简洁直观的Web界面
- **免费使用**：Google API 每日提供1,500次免费请求

## 注意事项

- 使用 Gemini 2.0 Flash 进行分析
- 需要稳定的网络连接
- 免费 API 使用额度 - Google 每日提供1,500次免费请求
- 仅供教育和开发目的使用
- 不能替代专业医疗诊断

## 免责声明

**重要提醒**：此工具仅供教育和信息参考目的。所有分析结果都应由合格的医疗专业人员审查。请勿仅基于此分析结果做出医疗决策。

## 开发者信息

- **框架**：基于 Agno 智能代理框架
- **模型**：Google Gemini 2.0 Flash
- **语言**：Python
- **界面**：Streamlit Web 应用

## 支持格式

- **图像格式**：JPG, JPEG, PNG, DICOM
- **影像类型**：X光、CT扫描、MRI、超声波等各种医疗影像

## 部署建议

1. **本地开发**：使用 `streamlit run` 命令
2. **云端部署**：可部署至 Streamlit Cloud、Heroku 等平台
3. **容器化**：支持 Docker 容器化部署
4. **负载均衡**：生产环境建议使用负载均衡器

---

*此项目是 awesome-llm-apps 系列的一部分，致力于展示 AI 在医疗健康领域的应用潜力。* 