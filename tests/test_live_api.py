import asyncio
import json
import uuid
import os
import sys
from pathlib import Path

# 将项目根目录添加到 sys.path
root_path = Path(__file__).parent.parent
sys.path.append(str(root_path))

from loguru import logger
from src.config.settings import settings
from src.agents.sqli.graph import sqli_graph
from src.agents.xss.graph import xss_graph

async def test_live_sqli_restful():
    """
    测试真实的 SQLi API 调用过程，验证：
    1. LLM 是否识别 RESTful 路径参数并生成 Payload
    2. 执行器是否正确替换占位符并发送请求
    3. 分析器在失败后是否给出反馈并触发重试
    """
    logger.info("🚀 开始实时 API 测试: SQLi RESTful 探测")
    
    # 使用一个真实的、安全的测试目标 (httpbin.org 会反射路径)
    # 模拟路径参数: /status/200 -> 我们期望识别到 200 并注入
    target_url = "https://httpbin.org/id/200"
    
    state = {
        "request_id": f"live-sqli-{uuid.uuid4().hex[:6]}",
        "target_url": target_url,
        "method": "POST",
        "headers": {
            "User-Agent": "WebAgent/1.0",
            "Accept": "application/json"
        },
        "body": json.dumps({"uid": 200}),
        "tasks": ["sqli"],
        "messages": [],
        "audit_log": [],
        "test_results": [],
        "sqli_retry_count": 0,
        "findings": []
    }

    try:
        # 执行 SQLi 图
        # 注意：这会产生真实的 LLM 费用和网络流量
        final_state = await sqli_graph.ainvoke(state)
        
        logger.success("✅ 实时 SQLi 测试执行完成")
        logger.info(f"最终判定: {final_state.get('next_step')}")
        logger.info(f"重试次数: {final_state.get('sqli_retry_count')}")
        
            
        # 检查审计日志 (已改为数据库存储)
        # audit_path = "logs/audit.jsonl"
        # if os.path.exists(audit_path):
        #    logger.info(f"📝 审计日志已记录至: {audit_path}")
        logger.info("📝 审计日志已存入数据库")
            
    except Exception as e:
        logger.error(f"❌ 实时测试出错: {e}")

async def test_live_xss_feedback():
    """
    测试 XSS 模块的反馈闭环
    """
    logger.info("🚀 开始实时 API 测试: XSS 反馈闭环")
    
    # 模拟一个会反射参数的接口
    # 修正：POST 请求应该发往 /post 端点，而非 /get
    target_url = "https://httpbin.org/post"
    
    state = {
        "request_id": f"live-xss-{uuid.uuid4().hex[:6]}",
        "target_url": target_url,
        "method": "POST",
        "headers": {},
        "body": json.dumps({"q": "test"}),
        "tasks": ["xss"],
        "messages": [],
        "audit_log": [],
        "test_results": [],
        "xss_retry_count": 0,
        "findings": []
    }

    try:
        final_state = await xss_graph.ainvoke(state)
        logger.success("✅ 实时 XSS 测试执行完成")
        logger.info(f"待探测参数/路径: {final_state.get('potential_points')}")
        if final_state.get("findings"):
            logger.warning(f"发现漏洞数量: {len(final_state['findings'])}")
        else:
            logger.info("未发现确认的 XSS 漏洞")
        
    except Exception as e:
        logger.error(f"❌ 实时测试出错: {e}")

async def main():
    # 检查 API Key
    if not settings.OPENAI_API_KEY or "sk-..." in settings.OPENAI_API_KEY:
        logger.error("❌ 未检测到有效的 OPENAI_API_KEY，请在 .env 文件中配置")
        return

    # 运行 SQLi 测试
    await test_live_sqli_restful()
    print("\n" + "="*50 + "\n")
    # 运行 XSS 测试
    await test_live_xss_feedback()

if __name__ == "__main__":
    # 确保日志目录存在
    os.makedirs("logs", exist_ok=True)
    asyncio.run(main())
