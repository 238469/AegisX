from langgraph.graph import StateGraph, END
from src.agents.xss.state import XSSState
from src.agents.xss.nodes import XSSNodes

def create_xss_graph():
    builder = StateGraph(XSSState)
    nodes = XSSNodes()

    # 添加节点
    builder.add_node("analyzer", nodes.analyze_injection_points)
    builder.add_node("strategist", nodes.strategist_node)
    builder.add_node("executor", nodes.executor_node)
    builder.add_node("final_analyzer", nodes.analyzer_node)

    # 条件边：如果在初始化阶段未发现注入点，直接结束
    def route_after_init(state: XSSState):
        if not state.get("potential_points"):
            from loguru import logger
            logger.info("未识别到潜在注入点，XSS 扫描提前结束。")
            return END
        return "strategist"

    # 编排流程
    builder.set_entry_point("analyzer")
    builder.add_conditional_edges("analyzer", route_after_init)
    builder.add_edge("strategist", "executor")
    builder.add_edge("executor", "final_analyzer")

    # 条件边：支持重试与循环限制
    def route_decision(state: XSSState):
        if state.get("next_step") == "found":
            return END
        if state["next_step"] == "retry":
            # 增加循环次数限制，防止死循环
            from src.config.settings import settings
            if state.get("xss_retry_count", 0) < settings.SCAN_MAX_RETRIES:
                return "strategist"
            else:
                from loguru import logger
                logger.warning(f"XSS 达到最大重试次数 ({state.get('xss_retry_count')})，强制结束。")
                return END
        return END

    builder.add_conditional_edges("final_analyzer", route_decision)

    return builder.compile()

xss_graph = create_xss_graph()
