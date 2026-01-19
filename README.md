# AegisIntelligence (AI-WebAgent) - AI 驱动的智能 Web 渗透测试进化系统

AegisIntelligence 是一款基于 **LangGraph** 和 **LLM (大语言模型)** 构建的下一代 Web 安全自动化渗透测试代理系统。它通过多智能体协作（Multi-Agent Collaboration）和反馈驱动的策略进化，模拟资深安全专家的思维逻辑，对目标进行深度漏洞探测。

## 🌟 核心特性

- **🤖 多智能体协同架构**：由 Manager Agent 统一调度，SQLi、XSS、Fuzz 等专项 Agent 协同工作，实现复杂漏洞的自动化发现。
- **📈 反馈驱动的策略进化**：系统不仅执行探测，还会根据每一轮的响应结果（延迟、长度差异、状态码等）动态调整 Payload 策略。
- **🚀 静态+动态双引擎**：
  - **首轮探测**：使用内置的高频静态 Payload 库进行快速覆盖。
  - **后续进化**：针对复杂场景，调用 LLM 生成具有针对性的绕过（Bypass）Payload。
- **📂 完善的项目管理与持久化**：
  - 基于 SQLite 的项目化存储，记录所有漏洞详情、原始请求/响应包。
  - 完整的 Agent 对话日志审计，确保测试过程可追溯。
- **🛡️ 强大的 WAF 绕过能力**：AI 会自动分析被拦截的特征，并尝试内联注释、等价函数替换、多重编码等绕过技术。

## 🏗️ 系统架构

- **Manager Agent**：任务分发与状态管理核心。
- **Strategist Node**：基于历史执行结果生成探测策略。
- **Executor Node**：高性能异步并发探测执行引擎。
- **Analyzer Node**：深度分析探测结果，判定漏洞并提供修复建议。
- **Persistence Layer**：基于项目维度的漏洞与日志持久化。

## 🛠️ 技术栈

- **Core**: Python 3.10+
- **Orchestration**: [LangGraph](https://github.com/langchain-ai/langgraph)
- **LLM Framework**: [LangChain](https://github.com/langchain-ai/langchain)
- **Database**: SQLite (SQLAlchemy)
- **Async Engine**: httpx
- **Logging**: Loguru & Custom Auditor

## 🚀 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 配置环境
在根目录创建 `.env` 文件并配置您的 API Key：
```env
OPENAI_API_KEY=your_key_here
OPENAI_API_BASE=https://api.openai.com/v1
MODEL_NAME_MANAGER=gpt-4o
MODEL_NAME_WORKER=gpt-4o-mini
```

### 3. 启动扫描
```bash
python main.py
```

## 📊 数据存储
漏洞结果和 Agent 日志将存储在 `data/webagent.db` 中。您可以通过项目名称查询特定的扫描记录。

---
**免责声明**：本工具仅用于授权的安全测试与教学研究，严禁用于任何非法的网络攻击活动。使用者需自行承担因使用本工具而产生的一切法律责任。
