from langgraph.graph import StateGraph, END
from src.agents.sqli.state import SQLiState
from src.agents.sqli.nodes import SQLiNodes

def create_sqli_graph():
    builder = StateGraph(SQLiState)
    nodes = SQLiNodes()

    # 添加所有节点
    builder.add_node("analyzer_init", nodes.analyze_injection_points)
    builder.add_node("strategist", nodes.strategist_node)
    builder.add_node("executor", nodes.executor_node)
    builder.add_node("analyzer", nodes.analyzer_node)

    # 条件边：如果在初始化阶段未发现注入点，直接结束
    def route_after_init(state: SQLiState):
        if not state.get("potential_points"):
            from loguru import logger
            logger.info("未识别到潜在注入点，SQLi 扫描提前结束。")
            return END
        return "strategist"

    # 编排流程
    builder.set_entry_point("analyzer_init")
    builder.add_conditional_edges("analyzer_init", route_after_init)
    builder.add_edge("strategist", "executor")
    builder.add_edge("executor", "analyzer")

    # 条件边：根据分析器的决策决定是否重试
    def route_decision(state: SQLiState):
        if state["next_step"] == "found":
            return END
        if state["next_step"] == "retry":
            # 增加循环次数限制，防止死循环
            from src.config.settings import settings
            if state.get("sqli_retry_count", 0) < settings.SCAN_MAX_RETRIES:
                return "strategist"
            else:
                from loguru import logger
                logger.warning(f"SQLi 达到最大重试次数 ({state.get('sqli_retry_count')})，强制结束。")
                return END
        return END

    builder.add_conditional_edges("analyzer", route_decision)

    return builder.compile()

sqli_graph = create_sqli_graph()
