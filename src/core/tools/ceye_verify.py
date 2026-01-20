import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from loguru import logger
from typing import Literal
from src.config.settings import settings

class CeyeVerifySchema(BaseModel):
    filter: str = Field(..., description="过滤关键词，用于匹配特定的 Payload 标识 (长度限制 20 字符)。例如: 'vuln_123'")
    type: Literal["dns", "http"] = Field("dns", description="查询类型: 'dns' 或 'http'。默认为 'dns'。")

@tool(args_schema=CeyeVerifySchema)
async def verify_oob_callback(filter: str, type: str = "dns") -> str:
    """
    通过 CEYE API 验证是否收到了带外 (OOB) 请求 (DNS/HTTP)。
    用于验证无回显漏洞 (如 Blind SQLi, Blind RCE, SSRF 等)。
    
    使用前请确保已在配置中设置 CEYE_API_TOKEN。
    """
    token = settings.CEYE_API_TOKEN
    if not token:
        return "❌ 错误: 未配置 CEYE_API_TOKEN。请在环境变量或配置文件中设置。"

    # CEYE API URL
    url = "http://api.ceye.io/v1/records"
    
    params = {
        "token": token,
        "type": type,
        "filter": filter
    }

    logger.info(f"正在查询 CEYE 记录: type={type}, filter={filter}")

    try:
        # 使用系统代理配置 (如果有)
        proxy = settings.SCAN_PROXY
        # 如果 proxy 是空字符串，设为 None 避免 httpx 报错
        if proxy == "":
            proxy = None
        
        async with httpx.AsyncClient(proxy=proxy, verify=False, timeout=10.0) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            
            try:
                data = resp.json()
            except ValueError:
                return f"❌ CEYE API 响应格式错误: {resp.text[:200]}"

            # CEYE API Response format:
            # {
            #   "meta": { "code": 200, "message": "OK" },
            #   "data": [ ... ]
            # }

            meta = data.get("meta", {})
            if meta.get("code") != 200:
                return f"❌ CEYE API 错误: {meta.get('message', 'Unknown Error')}"

            records = data.get("data", [])
            if not records:
                return f"[-] 未检测到包含 '{filter}' 的 {type.upper()} 记录。"

            # Format output
            result_msg = f"✅ 成功检测到 {len(records)} 条 OOB 记录 (Filter: {filter}):\n"
            
            for i, record in enumerate(records[:5]): # Limit to 5 details
                # Record fields: id, name, remote_addr, created_at
                name = record.get("name", "N/A")
                remote_addr = record.get("remote_addr", "N/A")
                created_at = record.get("created_at", "N/A")
                result_msg += f"\n{i+1}. [{created_at}] 来自 {remote_addr} -> {name}"
            
            if len(records) > 5:
                result_msg += f"\n\n... (还有 {len(records)-5} 条记录未显示)"

            return result_msg

    except Exception as e:
        logger.error(f"CEYE API 查询失败: {e}")
        return f"❌ 查询失败: {str(e)}"
