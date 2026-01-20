import redis
import json
from src.config.settings import settings

class RedisHelper:
    """Redis 工具类，负责指纹存储和任务队列操作"""
    
    def __init__(self):
        self.client = redis.from_url(settings.REDIS_URL, decode_responses=True)
        self.fingerprint_key = "webagent:fingerprints"
        self.queue_key = "webagent:tasks:initial"

    def is_duplicate(self, fingerprint: str) -> bool:
        """检查指纹是否已存在（去重）"""
        return self.client.sismember(self.fingerprint_key, fingerprint)

    def add_fingerprint(self, fingerprint: str):
        """记录新指纹"""
        self.client.sadd(self.fingerprint_key, fingerprint)

    def push_task(self, task_data: dict):
        """将任务推送到初始队列"""
        self.client.rpush(self.queue_key, json.dumps(task_data))
        
        # [高级功能] 提取并存储 Host 级别的历史参数
        # 目的：为 Fuzz 模块提供上下文，构建 Host -> Params Set 映射
        try:
            url = task_data.get("url", "")
            method = task_data.get("method", "GET")
            body = task_data.get("body", "")
            headers = task_data.get("headers", {})
            
            # 提取 Host
            host = headers.get("Host")
            if not host and url:
                if "://" in url:
                    host = url.split("/")[2]
                else:
                    # 处理无 scheme 的情况，假设它是 host/path
                    host = url.split("/")[0]
            
            # 提取参数逻辑
            params = set()
            
            # 1. URL Query 参数
            if "?" in url:
                try:
                    query = url.split("?")[1]
                    for pair in query.split("&"):
                        if "=" in pair:
                            key = pair.split("=")[0]
                            if key:
                                params.add(key)
                except Exception:
                    pass
            
            # 2. Body 参数 (JSON/Form)
            if body:
                if isinstance(body, str):
                    body = body.strip()
                    if body.startswith("{"):
                        try:
                            json_body = json.loads(body)
                            if isinstance(json_body, dict):
                                params.update(json_body.keys())
                        except Exception:
                            pass
                    # 尝试 Form 表单 (key=value&key2=value2)
                    elif "=" in body: 
                        try:
                            for pair in body.split("&"):
                                if "=" in pair:
                                    key = pair.split("=")[0]
                                    if key:
                                        params.add(key)
                        except Exception:
                            pass
                elif isinstance(body, dict):
                     params.update(body.keys())

            if params and host:
                # 存储到 Set 中，自动去重
                redis_key = f"webagent:host:{host}:params"
                self.client.sadd(redis_key, *params)
        except Exception as e:
            # 记录日志但不要阻断主流程
            # 在实际生产中这里应该使用 logger
            print(f"Error extracting history params: {e}")

    def get_host_params(self, host: str) -> list:
        """获取指定 Host 的历史参数列表"""
        return list(self.client.smembers(f"webagent:host:{host}:params"))

    def publish_log(self, message: str):
        """发布实时日志到 Redis Channel"""
        self.client.publish("webagent:logs", message)

# 单例模式供全局使用
redis_helper = RedisHelper()
