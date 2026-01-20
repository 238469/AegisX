from typing import List, Union, Any, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator

class Settings(BaseSettings):
    # LLM 配置
    OPENAI_API_KEY: str = Field(default="sk-...", description="OpenAI API Key")
    OPENAI_API_BASE: str = Field(default="https://api.openai.com/v1", description="OpenAI API Base URL")
    MODEL_NAME_MANAGER: str = Field(default="gpt-4o", description="Manager 节点使用的模型")
    MODEL_NAME_WORKER: str = Field(default="gpt-3.5-turbo", description="Worker 节点使用的模型")

    # 代理配置
    MITM_PROXY_PORT: int = Field(default=8080, description="Mitmproxy 监听端口")
    
    # 扫描控制
    SCAN_PROXY: Optional[str] = Field(default=None, description="扫描探测时使用的代理 (例如 http://127.0.0.1:8080)")
    SCAN_MAX_TASKS: int = Field(default=3, description="最大并发扫描任务数 (同时处理多少个流量)")
    SCAN_MAX_CONCURRENCY: int = Field(default=5, description="单个扫描任务内的最大并发探测数")
    SCAN_MAX_RETRIES: int = Field(default=3, description="每个参数的最大重试轮数")
    SCAN_TIMEOUT: float = Field(default=10.0, description="请求超时时间")

    # 目标限制
    TARGET_WHITELIST: Any = Field(
        default_factory=list, 
        description="允许扫描的 IP 或域名白名单"
    )

    @field_validator("TARGET_WHITELIST", mode="before")
    @classmethod
    def parse_whitelist(cls, v: Any) -> List[str]:
        if isinstance(v, str):
            # 处理逗号分隔的字符串
            return [item.strip() for item in v.split(",") if item.strip()]
        if isinstance(v, list):
            return v
        return []

    # 存储配置
    REDIS_URL: str = Field(default="redis://localhost:6379/0", description="Redis 连接地址")

    # OOB (带外) 验证配置
    CEYE_API_TOKEN: Optional[str] = Field(default=None, description="CEYE API Token")
    CEYE_IDENTIFIER: Optional[str] = Field(default=None, description="CEYE Identifier (e.g., xxxx.ceye.io)")

    # 日志配置
    LOG_LEVEL: str = Field(default="INFO", description="日志级别")
    LOG_PROMPT_INTERACTION: bool = Field(default=True, description="是否记录全量 Prompt 交互")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

# 全局配置实例
settings = Settings()
