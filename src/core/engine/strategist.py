import json
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from src.config.settings import settings
from src.utils.auditor import auditor
from src.core.llm.service import create_audited_llm
from loguru import logger

class GenericStrategist:
    """
    通用策略生成引擎：根据不同的提示词生成特定漏洞的测试用例
    """
    def __init__(self):
        self.audited_llm = create_audited_llm(
            model_name=settings.MODEL_NAME_WORKER,
            api_key=settings.OPENAI_API_KEY,
            api_base=settings.OPENAI_API_BASE,
            model_kwargs={"response_format": {"type": "json_object"}}
        )

    def generate(self, vuln_type: str, system_prompt: str, user_context: dict, request_id: str, project_name: str = "Default") -> list:
        """
        通用生成方法
        :param vuln_type: 漏洞类型 (如 "SQLi", "XSS")
        :param system_prompt: 专门针对该漏洞的系统提示词
        :param user_context: 包含 url, points, original_body, feedback, full_request 等的上下文
        :param request_id: 任务 ID
        :param project_name: 项目名称
        """
        user_prompt = "目标 URL: {url}\n待测试参数: {points}\n"
        feedback = user_context.get("feedback")
        if feedback:
            if isinstance(feedback, list):
                feedback_str = "\n".join([f"- {f}" for f in feedback])
                user_prompt += "历史轮次分析反馈汇总（请参考这些反馈不断优化绕过策略）:\n{feedback}\n"
            else:
                feedback_str = feedback
                user_prompt += "上轮分析反馈（请根据此反馈调整策略）: {feedback}\n"
        else:
            feedback_str = ""
        
        # 注入历史执行结果 (包含所有历史轮次数据，用于进化策略)
        history_results = user_context.get("history_results")
        if history_results:
            user_prompt += "历史探测执行结果汇总（包含最近多轮的详细响应指标，请根据这些数据的变化趋势调整并进化你的 Payload 策略）:\n{history_results}\n"

        if user_context.get("full_request"):
            user_prompt += "原始完整请求上下文: {full_request}\n"
            
        user_prompt += "原始响应片段: {orig}"

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", user_prompt)
        ])
        
        chain = prompt | self.audited_llm.llm
        inputs = {
            "url": user_context.get("url", ""),
            "points": ", ".join(user_context.get("points", [])),
            "orig": user_context.get("orig", "")[:500],
            "feedback": feedback_str,
            "history_results": json.dumps(user_context.get("history_results", []), ensure_ascii=False),
            "full_request": json.dumps(user_context.get("full_request", {}), ensure_ascii=False)
        }
        
        try:
            response = self.audited_llm.invoke(
                chain=chain,
                inputs=inputs,
                agent_name=f"{vuln_type}_Strategist",
                task_id=request_id,
                prompt_template=prompt,
                project_name=project_name
            )
            
            data = json.loads(response.content)
            test_cases = data.get("test_cases", [])
            
            logger.info(f"[{vuln_type}] 策略生成完成 | 数量: {len(test_cases)}")
            if not test_cases:
                logger.warning(f"[{vuln_type}] LLM 未生成任何测试用例。响应内容: {response.content}")
            
            return test_cases
        except Exception as e:
            logger.error(f"[{vuln_type}] 生成 Payload 失败: {e}")
            return []
