import sys
import asyncio
from pathlib import Path
from loguru import logger

# Add project root to sys.path
root_path = Path(__file__).parent.parent
sys.path.append(str(root_path))

from src.agents.manager.graph import graph

async def test_agent_get_request():
    """
    直接调用 Agent 图测试 GET 请求
    不依赖 Proxy，直接模拟一个 HTTP 请求 State 传入 Manager Agent
    """
    # 1. 构造模拟的 GET 请求 State
    # 使用 httpbin.org 作为测试目标，因为它稳定且公网可达
    target_url = "http://httpbin.org/get?id=1&name=test_user&q=search_term"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) TestAgent/1.0",
        "Accept": "application/json"
    }

    state = {
        "request_id": "test-agent-get-001",
        "target_url": target_url,
        "method": "GET",
        "headers": headers,
        "body": None,  # GET 请求通常没有 Body
        "tasks": None, # 初始为空，由 Manager 分析生成
        "messages": [],
        "audit_log": [],
        "test_results": [],
        "findings": []
    }

    logger.info(f"🚀 开始 Agent 直接测试")
    logger.info(f"🎯 目标: {target_url}")
    logger.info(f"ℹ️ 说明: 此脚本直接调用 Agent 逻辑链，模拟完整扫描流程")

    try:
        # 2. 调用 Agent 主图 (Manager -> Worker -> Analyzer)
        # ainvoke 会自动执行 graph 中定义的状态流转
        final_state = await graph.ainvoke(state)
        
        logger.info("✅ Agent 执行完成")
        
        # 3. 输出执行结果
        tasks = final_state.get("tasks", [])
        if tasks:
            logger.info(f"📋 Manager 分配的任务: {tasks}")
        else:
            logger.warning("⚠️ Manager 未识别出需要扫描的任务 (可能是 Prompt 判断无风险)")

        findings = final_state.get("findings", [])
        if findings:
            logger.success(f"🎉 发现漏洞: {len(findings)} 个")
            for f in findings:
                logger.success(f"   - 类型: {f.get('vuln_type', 'Unknown')}")
                logger.success(f"   - 参数: {f.get('parameter', 'Unknown')}")
                logger.success(f"   - Payload: {f.get('payload', 'Unknown')}")
        else:
            logger.info("🛡️ 未发现漏洞 (符合预期，因为 httpbin 是安全的)")
            
        # 打印部分调试信息
        if final_state.get("test_results"):
             logger.debug(f"🔍 总计执行探测次数: {len(final_state['test_results'])}")

    except Exception as e:
        logger.error(f"❌ Agent 执行出错: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(test_agent_get_request())
