from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from src.config.settings import settings
from src.utils.auditor import auditor
from src.core.llm.service import create_audited_llm
from src.agents.manager.state import AgentState
from loguru import logger

class ManagerAgent:
    """
    顶级决策者：负责流量分析与任务分发
    """
    def __init__(self):
        self.audited_llm = create_audited_llm(
            model_name=settings.MODEL_NAME_MANAGER,
            api_key=settings.OPENAI_API_KEY,
            api_base=settings.OPENAI_API_BASE
        )
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个资深安全分析专家。请分析以下 HTTP 请求和响应上下文，判断其可能存在的漏洞（sqli, xss, fuzz）。
你的分析应基于：
1. URL 和 Body 中的参数名及其值。
2. 请求头（Headers）中的敏感字段，如 User-Agent, Referer, Cookie, X-Forwarded-For 等。
3. 响应上下文（如果提供），如 Server 头、响应内容中是否包含报错、反射等。

任务类型说明：
- **sqli**: 存在数据库交互迹象，如 id, search, filter 参数。
- **xss**: 存在输入回显迹象，如 q, name, message 参数。
- **fuzz**: **参数与值模糊测试**。专注于发现隐藏参数（Parameter Discovery）和枚举敏感业务值（Value Fuzzing）。任何看似重要的接口（如支付、权限、查询），或者可能存在隐藏参数时，都**必须**包含 fuzz 任务。

决策原则（支持多任务并发）：
- 如果一个请求既有 ID 参数（可能 SQLi），又有回显参数（可能 XSS），同时业务逻辑复杂（需要 Fuzz），请**同时输出**这三者。
- 不要犹豫，宁可多测不可漏测。

输出要求：
1. 仅输出漏洞类型列表，用逗号分隔（如: sqli,fuzz,xss）。
2. 如果认为不存在漏洞风险，输出 'none'。
3. 即使请求没有参数，也要关注请求头注入的可能性。"""),
            ("user", "### Request\nMethod: {method}\nURL: {url}\nHeaders: {headers}\nBody: {body}\n\n### Response (Context)\nHeaders: {res_headers}\nBody: {res_body}")
        ])

    async def analyze_request(self, state: AgentState) -> dict:
        """分析请求并决定攻击任务"""
        # 1. 安全校验 (AI 层的二次确认)
        host = state["target_url"].split("/")[2] if "://" in state["target_url"] else state["target_url"]
        if not any(item in host for item in settings.TARGET_WHITELIST):
            logger.warning(f"AI 层拦截：目标 {host} 不在白名单中！")
            return {"tasks": [], "messages": [("assistant", "目标不在白名单，拒绝处理")]}

        # 2. 调用 LLM 决策
        chain = self.prompt | self.audited_llm.llm
        inputs = {
            "method": state["method"],
            "url": state["target_url"],
            "headers": str(state["headers"]),
            "body": state["body"] or "None",
            "res_headers": str(state.get("response_headers", "None")),
            "res_body": state.get("response_body", "None")
        }
        
        response = await self.audited_llm.ainvoke(
            chain=chain,
            inputs=inputs,
            agent_name="Manager",
            task_id=state["request_id"],
            prompt_template=self.prompt,
            project_name=state.get("project_name", "Default")
        )

        # 4. 解析任务
        content = response.content.strip().lower()
        if content == "none":
            tasks = []
        else:
            tasks = [t.strip() for t in content.split(",") if t.strip()]
        
        logger.info(f"Manager 决策完成，识别到潜在漏洞类型: {tasks}")
        
        return {
            "tasks": tasks, 
            "messages": [response],
            "sqli_retry_count": 0,
                "xss_retry_count": 0,
                "fuzz_retry_count": 0,
                "analysis_feedback": []
            }
