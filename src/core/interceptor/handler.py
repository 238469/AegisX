import hashlib
from mitmproxy import http
from src.config.settings import settings
from src.utils.redis_helper import redis_helper
from loguru import logger

class InterceptorHandler:
    """流量处理核心逻辑"""

    def __init__(self):
        logger.info(f"拦截器初始化成功，当前白名单: {settings.TARGET_WHITELIST}")

    @staticmethod
    def is_in_whitelist(host: str) -> bool:
        """校验目标 Host 是否在白名单中"""
        if not settings.TARGET_WHITELIST:
            return False
        return any(item in host for item in settings.TARGET_WHITELIST)

    @staticmethod
    def calculate_fingerprint(flow: http.HTTPFlow) -> str:
        """
        计算请求指纹: URL + Method + Params + Body(Hash)
        """
        request = flow.request
        # 基础部分
        base_str = f"{request.method}|{request.pretty_url}"
        
        # 处理 Body
        body_hash = hashlib.md5(request.content).hexdigest() if request.content else "empty"
        
        full_str = f"{base_str}|{body_hash}"
        return hashlib.sha256(full_str.encode()).hexdigest()

    def process_flow(self, flow: http.HTTPFlow):
        """处理单个流量对象"""
        host = flow.request.pretty_host
        
        # 1. 白名单过滤
        if not self.is_in_whitelist(host):

            return

        logger.debug(f"正在处理白名单请求: {host}")

        # 2. 静态资源过滤 (简单扩展名过滤)
        if any(flow.request.path.endswith(ext) for ext in ['.js', '.css', '.png', '.jpg', '.gif', '.svg', '.woff','.woff2','.ico']):
            return

        # 3. 计算指纹并去重
        fingerprint = self.calculate_fingerprint(flow)
        if redis_helper.is_duplicate(fingerprint):
            logger.debug(f"跳过重复请求: {flow.request.pretty_url}")
            return

        # 4. 获取当前活跃项目名称 (从 Redis 中动态获取)
        project_name = redis_helper.client.get("webagent:current_project") or "Default"

        # 5. 构建 InitialState 对象
        task_data = {
            "project_name": project_name,
            "url": flow.request.pretty_url,
            "method": flow.request.method,
            "headers": dict(flow.request.headers),
            "body": flow.request.text if flow.request.text else "",
            "response_headers": dict(flow.response.headers) if flow.response else {},
            "response_body": flow.response.text if flow.response and flow.response.text else "",
            "fingerprint": fingerprint
        }

        # 6. 持久化指纹并推送任务
        redis_helper.add_fingerprint(fingerprint)
        redis_helper.push_task(task_data)
        
        logger.info(f"已捕获并推送新任务 [{project_name}]: [{flow.request.method}] {flow.request.pretty_url}")
