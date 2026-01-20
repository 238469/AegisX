import sys
import os
import subprocess
import time
import asyncio
from multiprocessing import Process
from loguru import logger

# 确保项目根目录在 path 中
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from src.core.engine.runner import TaskRunner
from src.config.settings import settings
from src.utils.db_helper import db_helper
from src.utils.redis_helper import redis_helper

def setup_logging():
    """配置日志输出到文件和 Redis"""
    log_dir = os.path.join(os.path.dirname(__file__), "logs")
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
        
    # 1. 添加文件输出
    logger.add(
        os.path.join(log_dir, "webagent.log"),
        rotation="10 MB",
        retention="1 week",
        level="INFO",
        encoding="utf-8",
        enqueue=True
    )
    
    # 2. 添加 Redis Sink 用于前端实时日志显示
    def redis_sink(message):
        try:
            # 提取日志文本
            log_text = message.record["message"]
            level = message.record["level"].name
            # 构建简化的 JSON 格式推送给前端
            payload = {
                "time": message.record["time"].strftime("%H:%M:%S"),
                "level": level,
                "content": log_text
            }
            redis_helper.publish_log(json.dumps(payload))
        except Exception:
            pass

    logger.add(redis_sink, level="INFO")

def run_api():
    """启动 FastAPI 后端服务"""
    logger.info("正在启动 API 服务 (端口: 8000)...")
    import uvicorn
    from src.api.main import app
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="error")

def run_mitmproxy():
    """启动 mitmproxy 拦截器"""
    logger.info(f"正在启动 mitmproxy 拦截器 (端口: {settings.MITM_PROXY_PORT})...")
    addon_path = os.path.join("src", "core", "interceptor", "addons.py")
    
    # 使用 subprocess 启动 mitmdump
    cmd = [
        "mitmdump",
        "-q",  # 静默模式，不打印流量日志
        "-s", addon_path,
        "-p", str(settings.MITM_PROXY_PORT)
    ]
    
    try:
        process = subprocess.Popen(cmd)
        process.wait()
    except Exception as e:
        logger.error(f"mitmproxy 启动失败: {e}")

def run_task_runner():
    """启动任务处理器 (异步运行)"""
    setup_logging()
    logger.info("正在启动任务处理器...")
    try:
        runner = TaskRunner()
        asyncio.run(runner.run())
    except Exception as e:
        logger.error(f"任务处理器运行异常: {e}")

def main():
    setup_logging()
    logger.info("=== WebAgent 综合扫描系统启动 ===")
    
    # 创建子进程
    p_mitm = Process(target=run_mitmproxy)
    p_runner = Process(target=run_task_runner)
    p_api = Process(target=run_api)
    
    # 设置为守护进程
    p_mitm.daemon = True
    p_runner.daemon = True
    p_api.daemon = True
    
    try:
        p_api.start()
        p_mitm.start()
        time.sleep(2)
        p_runner.start()
        
        logger.success("所有组件已启动！按 Ctrl+C 停止系统。")
        
        while True:
            time.sleep(1)
            if not p_mitm.is_alive():
                logger.error("mitmproxy 进程已意外退出")
                break
            if not p_runner.is_alive():
                logger.error("任务处理器进程已意外退出")
                break
            if not p_api.is_alive():
                logger.error("API 服务进程已意外退出")
                break
                
    except KeyboardInterrupt:
        logger.info("\n正在停止系统...")
        # 打印汇总信息
        try:
            summary = db_helper.get_session_summary()
            print(summary)
        except Exception as e:
            logger.error(f"生成汇总报告失败: {e}")
    finally:
        if p_mitm.is_alive():
            p_mitm.terminate()
        if p_runner.is_alive():
            p_runner.terminate()
        logger.info("系统已关闭。")

if __name__ == "__main__":
    main()
