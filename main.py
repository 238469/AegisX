import sys
import os
import time
import asyncio
from loguru import logger

# 确保项目根目录在 path 中
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from src.utils.logger_config import setup_logging
from src.core.engine.manager import scanner_manager

def run_api():
    """启动 FastAPI 后端服务"""
    import uvicorn
    from src.api.main import app
    logger.info("正在启动 API 服务 (端口: 8000)...")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

def main():
    # 初始化日志
    setup_logging()
    
    logger.info("=== WebAgent 综合扫描系统启动 ===")
    
    try:
        
        # 启动 API 服务 (当前进程运行)
        run_api()
        
    except KeyboardInterrupt:
        logger.info("\n正在停止系统...")
    finally:
        # 确保所有子进程都已关闭
        scanner_manager.stop_all()
        logger.info("系统已关闭。")

if __name__ == "__main__":
    main()
