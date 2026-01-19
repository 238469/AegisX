from typing import Annotated, List, TypedDict, Optional
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
import operator

def reduce_overwrite(left, right):
    """
    覆盖策略：并发写入时，保留非空的新值。
    如果都是相同的值，直接返回。
    """
    if right is None:
        return left
    return right

class AgentState(TypedDict):
    """
    全局 Agent 状态定义
    """
    # 原始请求信息 (来自拦截器)
    request_id: Annotated[str, reduce_overwrite]
    project_name: Annotated[str, reduce_overwrite] # 新增：项目名称
    target_url: Annotated[str, reduce_overwrite]
    method: Annotated[str, reduce_overwrite]
    headers: Annotated[dict, reduce_overwrite]
    body: Annotated[Optional[str], reduce_overwrite]
    
    # 原始响应信息 (如果可用)
    response_headers: Annotated[Optional[dict], reduce_overwrite]
    response_body: Annotated[Optional[str], reduce_overwrite]
    
    # 任务分发状态
    tasks: Annotated[List[str], reduce_overwrite]  # 例如: ["sqli", "xss"]
    
    # 消息记录 (用于 LangGraph 内部通信)
    messages: Annotated[List[BaseMessage], add_messages]

    # 分析反馈记忆 (列表形式以支持多轮追溯)
    analysis_feedback: Annotated[List[str], operator.add]

    # 漏洞发现汇总
    findings: Annotated[List[dict], operator.add]

    # 历史探测执行结果汇总 (用于指导策略进化)
    history_results: Annotated[List[dict], operator.add]

    # 并发任务重试计数 (隔离)
    sqli_retry_count: Annotated[int, reduce_overwrite]
    xss_retry_count: Annotated[int, reduce_overwrite]
    fuzz_retry_count: Annotated[int, reduce_overwrite]
