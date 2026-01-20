import os
import json
from loguru import logger
from src.utils.redis_helper import redis_helper

def setup_logging(level="DEBUG"):
    """配置日志输出到控制台、文件和 Redis"""
    # 移除所有默认处理器
    logger.remove()
    
    # 1. 控制台输出 (带颜色)
    logger.add(
        sink=lambda msg: print(msg, end=""),
        level=level,
        colorize=True,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )

    # 2. 文件输出
    log_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../logs"))
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
        
    logger.add(
        os.path.join(log_dir, "webagent.log"),
        rotation="10 MB",
        retention="1 week",
        level=level,
        encoding="utf-8",
        enqueue=True
    )
    
    # 3. Redis Sink 用于前端实时日志显示
    def redis_sink(message):
        try:
            record = message.record
            # 构建简化的 JSON 格式推送给前端
            payload = {
                "time": record["time"].strftime("%H:%M:%S"),
                "level": record["level"].name,
                "content": record["message"]
            }
            redis_helper.publish_log(json.dumps(payload))
        except Exception:
            pass

    logger.add(redis_sink, level=level)
    
    logger.info(f"日志系统初始化完成 (级别: {level})")
