import sys
import os
import asyncio
from loguru import logger

# 确保项目根目录在 path 中
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from src.core.engine.runner import TaskRunner
from src.utils.logger_config import setup_logging

async def main():
    setup_logging()
    logger.info("TaskRunner 子进程已启动")
    try:
        runner = TaskRunner()
        await runner.run()
    except Exception as e:
        logger.error(f"TaskRunner 运行异常: {e}")

if __name__ == "__main__":
    asyncio.run(main())