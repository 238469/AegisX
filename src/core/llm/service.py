import json
from typing import Any, Dict, Optional, Union
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from src.utils.auditor import auditor
from loguru import logger

class AuditedLLM:
    """
    包装 LLM 调用，底层自动集成审计日志记录
    """
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm

    def _format_prompt(self, prompt: ChatPromptTemplate, inputs: Dict[str, Any]) -> str:
        """尝试格式化提示词用于日志记录"""
        try:
            return prompt.format(**inputs)
        except Exception as e:
            logger.debug(f"格式化审计提示词失败: {e}")
            return str(inputs)

    def invoke(self, 
               chain: Any, 
               inputs: Dict[str, Any], 
               agent_name: str, 
               task_id: str, 
               prompt_template: Optional[ChatPromptTemplate] = None,
               project_name: str = "Default") -> Any:
        """
        同步调用并记录日志
        """
        response = chain.invoke(inputs)
        
        # 记录审计
        prompt_str = self._format_prompt(prompt_template, inputs) if prompt_template else str(inputs)
        auditor.record(
            agent_name=agent_name,
            task_id=task_id,
            prompt=prompt_str,
            response=response.content if hasattr(response, 'content') else str(response),
            project_name=project_name
        )
        return response

    async def ainvoke(self, 
                      chain: Any, 
                      inputs: Dict[str, Any], 
                      agent_name: str, 
                      task_id: str, 
                      prompt_template: Optional[ChatPromptTemplate] = None,
                      project_name: str = "Default") -> Any:
        """
        异步调用并记录日志
        """
        response = await chain.ainvoke(inputs)
        
        # 记录审计
        prompt_str = self._format_prompt(prompt_template, inputs) if prompt_template else str(inputs)
        auditor.record(
            agent_name=agent_name,
            task_id=task_id,
            prompt=prompt_str,
            response=response.content if hasattr(response, 'content') else str(response),
            project_name=project_name
        )
        return response

def create_audited_llm(model_name: str, api_key: str, api_base: str, **kwargs) -> AuditedLLM:
    """工厂方法创建带审计的 LLM 实例"""
    llm = ChatOpenAI(
        model=model_name,
        openai_api_key=api_key,
        openai_api_base=api_base,
        **kwargs
    )
    return AuditedLLM(llm)
