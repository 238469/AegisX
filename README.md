# AegisX - AI 驱动的智能 Web 渗透测试进化系统

AegisX 是一款基于 **LangGraph** 和 **LLM (大语言模型)** 构建的下一代 Web 安全自动化渗透测试代理系统。它通过多智能体协作（Multi-Agent Collaboration）和反馈驱动的策略进化，模拟资深安全专家的思维逻辑，对目标进行深度漏洞探测。

## 🌟 核心特性

- **🤖 多智能体协同架构**：由 Manager Agent 统一调度，SQLi、XSS、Fuzz 等专项 Agent 协同工作，实现复杂漏洞的自动化发现。
- **📈 反馈驱动的策略进化**：系统不仅执行探测，还会根据每一轮的响应结果（延迟、长度差异、状态码等）动态调整 Payload 策略。
- **🧠 记忆与去重系统 (Redis)**：
  - **流量去重**：基于 Redis 存储请求指纹（Fingerprint），确保在复杂扫描任务中不重复处理相同接口。
  - **历史记忆**：自动提取并存储每个 Host 的历史参数集（Param Set），为 Fuzz 模块提供上下文支撑。
- **🚀 静态+动态双引擎**：
  - **首轮探测**：使用内置的高频静态 Payload 库进行快速覆盖。
  - **后续进化**：针对复杂场景，调用 LLM 生成具有针对性的绕过（Bypass）Payload。
- **📂 完善的项目管理与持久化**：
  - 基于 SQLite 的项目化存储，记录所有漏洞详情、原始请求/响应包。
  - 完整的 Agent 对话日志审计，确保测试过程可追溯。

## 🛠️ 扩展 AI 工具箱

系统内置了丰富的 AI 可调用工具，赋予 Agent 强大的实战能力：

- **🌐 HTTP/HTTPS 请求执行器**：
  - 支持完整的 HTTP 协议交互，自动处理 Host 头和 HTTPS 握手。
  - 集成 **系统代理 (System Proxy)**，确保流量可控。
- **🐍 Code Interpreter (代码解释器)**：
  - 提供安全的 Python 代码执行沙箱，Agent 可编写脚本进行复杂计算或逻辑验证。
- **🔍 Web Search (联网搜索)**：
  - 集成 DuckDuckGo 搜索能力，支持实时获取互联网信息和最新漏洞情报。
- **💣 POC Library (漏洞情报库)**：
  - 直接对接漏洞情报库 (如 rss.biu.life)，支持按标签搜索实战 POC 代码。
- **📡 CEYE Verify (OOB 验证)**：
  - 集成 CEYE API，自动检测和验证 DNS/HTTP 带外请求 (Blind RCE/SSRF)。

## 🏗️ 系统架构

- **Manager Agent**：任务分发与状态管理核心。
- **Strategist Node**：基于历史执行结果生成探测策略。
- **Executor Node**：高性能异步并发探测执行引擎。
- **Analyzer Node**：深度分析探测结果，判定漏洞并提供修复建议。
- **Redis Cache/Storage**：负责指纹去重、任务队列缓存以及 Host 级别参数记忆。
- **Persistence Layer**：基于项目维度的漏洞与日志持久化。

## 💻 核心代码实现

为了方便理解系统的工作原理，以下展示了 AegisX 的部分核心逻辑：

### 1. 多智能体工作流 (LangGraph)
系统通过 `Manager` 节点分析原始流量，并根据识别出的攻击面动态调度不同的专项 Worker 子图。

```python
# src/agents/manager/graph.py
def create_manager_graph():
    builder = StateGraph(AgentState)
    manager = ManagerAgent()

    # 添加主节点与专项 Worker 节点
    builder.add_node("manager", manager.analyze_request)
    builder.add_node("sqli_worker", sqli_graph)
    builder.add_node("xss_worker", xss_graph)

    # 基于任务列表进行条件路由 (并发执行)
    def route_tasks(state: AgentState):
        destinations = []
        if "sqli" in state["tasks"]: destinations.append("sqli_worker")
        if "xss" in state["tasks"]: destinations.append("xss_worker")
        return destinations if destinations else END

    builder.add_conditional_edges("manager", route_tasks)
    return builder.compile()
```

### 2. Redis 记忆与指纹系统
利用 Redis 实现高效的流量去重和 Host 参数画像，避免重复扫描并增强 Fuzz 效果。

```python
# src/utils/redis_helper.py
def push_task(self, task_data: dict):
    # 1. 存储请求指纹，实现扫描去重
    self.client.sadd("webagent:fingerprints", task_data["fingerprint"])
    
    # 2. 提取并记忆 Host 级别的历史参数集
    host = extract_host(task_data["url"])
    params = extract_params(task_data)
    if params:
        self.client.sadd(f"webagent:host:{host}:params", *params)
```

### 3. 反馈驱动的策略进化 (Strategist)
Strategist 不仅仅生成 Payload，它还会参考 `history_results` 中每一轮的响应时间、长度变化和相似度趋势。

```python
# src/core/engine/strategist.py
def generate_strategy(self, user_context: dict):
    # 提取历史探测结果摘要
    history_summary = [
        {
            "payload": r["payload"],
            "elapsed": r["elapsed"], 
            "len_diff": r["len_diff"]
        } for r in user_context.get("history_results", [])
    ]
    
    # 将历史趋势作为 Context 喂给 LLM，实现“进化”探测
    user_prompt = f"历史探测执行趋势:\n{json.dumps(history_summary)}\n请根据以上结果调整绕过策略..."
    # ... 调用 LLM 返回优化后的 Payload
```

### 4. 异步并发执行引擎 (Executor)
利用 `httpx` 和 `asyncio.Semaphore` 实现高并发且受控的探测执行，支持 RESTful 路径、Query 和 Body 自动注入。

```python
# src/core/engine/executor.py
async def execute_batch(self, test_cases: List[Dict]):
    async with httpx.AsyncClient(verify=False, proxy=self.proxies) as client:
        # 使用信号量控制并发数，防止触发频率限制
        async with self.semaphore:
            tasks = [self._run_single_test(client, case) for case in test_cases]
            return await asyncio.gather(*tasks)
```

## �️ 技术栈

- **Core**: Python 3.11+
- **Orchestration**: [LangGraph](https://github.com/langchain-ai/langgraph)
- **LLM Framework**: [LangChain](https://github.com/langchain-ai/langchain)
- **Database**: SQLite (SQLAlchemy)
- **Cache & Memory**: **Redis** (指纹去重、参数记忆)
- **Async Engine**: httpx
- **Logging**: Loguru & Custom Auditor

## 🚀 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 环境准备
- 确保已安装并启动 **Redis** 服务。
- 在根目录创建 `.env` 文件并配置相关 Key：
```env
OPENAI_API_KEY=your_key_here
OPENAI_API_BASE=https://api.openai.com/v1
MODEL_NAME_MANAGER=gpt-4o
MODEL_NAME_WORKER=gpt-4o-mini
REDIS_URL=redis://localhost:6379/0
# 可选配置
SCAN_PROXY=http://127.0.0.1:8080  # 系统扫描代理
CEYE_API_TOKEN=your_token_here    # CEYE OOB 验证 Token
CEYE_IDENTIFIER=your_id.ceye.io   # CEYE Identifier
```

### 3. 启动系统

本项目采用前后端分离架构，需分别启动后端服务和前端界面。

#### 3.1 启动后端 (API & Engine)
```bash
python main.py
```
后端服务将在 `http://localhost:8000` 启动，包含：
- FastAPI 接口服务
- Agent 扫描引擎
- Mitmproxy 流量监听 (默认端口 8080)

#### 3.2 启动前端 (Web UI)
```bash
cd frontend
npm install
npm run dev
```
前端界面将在 `http://localhost:5173` 启动。请在浏览器中访问此地址以使用图形化界面管理扫描任务和查看报告。

## 📊 数据存储
漏洞结果和 Agent 日志将存储在 `data/webagent.db` 中。您可以通过项目名称查询特定的扫描记录。

---
**免责声明**：本工具仅用于授权的安全测试与教学研究，严禁用于任何非法的网络攻击活动。使用者需自行承担因使用本工具而产生的一切法律责任。
