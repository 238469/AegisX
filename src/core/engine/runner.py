import json
import time
import uuid
import asyncio
from loguru import logger
from src.utils.redis_helper import RedisHelper
from src.agents.manager.graph import graph
from src.agents.manager.state import AgentState
from src.core.report_generator import ReportGenerator
from src.config.settings import settings

class TaskRunner:
    """
    任务运行器：从 Redis 提取任务并驱动 Agent 运行
    """
    def __init__(self):
        self.redis = RedisHelper()
        self.queue_key = "webagent:tasks:initial"
        self.report_gen = ReportGenerator()
        # 引入信号量限制并发任务数
        self.semaphore = asyncio.Semaphore(settings.SCAN_MAX_TASKS)
        logger.info(f"TaskRunner 初始化成功，最大并发任务数: {settings.SCAN_MAX_TASKS}")

    async def _process_task(self, request: dict):
        """处理单个任务的协程"""
        async with self.semaphore:
            try:
                # 初始化 Agent 状态
                initial_state: AgentState = {
                    "request_id": str(uuid.uuid4()),
                    "project_name": request.get("project_name", "Default"), # 提取项目名称
                    "target_url": request["url"],
                    "method": request["method"],
                    "headers": request.get("headers", {}),
                    "body": request.get("body"),
                    "response_headers": request.get("response_headers", {}),
                    "response_body": request.get("response_body", ""),
                    "tasks": [],
                    "messages": [],
                    "audit_log": [],
                    "findings": [],
                    "history_results": [],
                    "sqli_retry_count": 0,
            "xss_retry_count": 0,
            "fuzz_retry_count": 0,
            "analysis_feedback": []
        }
                
                logger.info(f"开始处理任务: {initial_state['request_id']} | {initial_state['method']} {initial_state['target_url']}")
                
                # 驱动 LangGraph 异步运行
                final_state = await graph.ainvoke(initial_state)
                
                # 生成报告
                findings = final_state.get("findings", [])
                if findings:
                    report_path = self.report_gen.generate(
                        findings, 
                        initial_state["request_id"],
                        initial_state.get("project_name", "Default")
                    )
                    logger.success(f"发现漏洞！报告已生成: {report_path}")
                else:
                    logger.info(f"未发现漏洞: {initial_state['request_id']}")
                
                logger.success(f"任务处理完成: {initial_state['request_id']} | 识别任务: {final_state.get('tasks', [])}")
                
            except Exception as e:
                logger.exception(f"处理任务时发生异常: {str(e)}")

    async def run(self):
        logger.info("Task Runner 启动，正在监听任务队列...")
        loop = asyncio.get_event_loop()
        
        while True:
            try:
                # 从 Redis 队列中获取任务 (阻塞式获取)
                task_data = await loop.run_in_executor(None, self.redis.client.blpop, self.queue_key, 5)
                
                if not task_data:
                    continue

                # 解析原始请求数据
                _, raw_request = task_data
                request = json.loads(raw_request)
                
                # 异步启动任务，不等待它完成
                asyncio.create_task(self._process_task(request))
                
            except Exception as e:
                logger.error(f"TaskRunner 运行异常: {e}")
                await asyncio.sleep(1)

if __name__ == "__main__":
    runner = TaskRunner()
    asyncio.run(runner.run())
