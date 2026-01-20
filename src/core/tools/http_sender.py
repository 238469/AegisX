import httpx
import re
from typing import Optional, Tuple, Dict
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from loguru import logger
from src.config.settings import settings

def parse_raw_request(raw_request: str, scheme: str = "http", target_host: Optional[str] = None) -> Tuple[str, str, Dict[str, str], str]:
    """
    解析原始 HTTP 请求字符串
    
    Args:
        raw_request: 原始请求报文
        scheme: 默认协议 (http/https)
        target_host: 目标主机 (如果指定，将替换原请求中的 Host)
        
    Returns:
        (method, url, headers, body)
    """
    lines = raw_request.strip().splitlines()
    if not lines:
        raise ValueError("空的请求内容")

    # 1. 解析请求行
    request_line = lines[0].strip()
    # 匹配: METHOD URL HTTP/VERSION 或 METHOD URL
    match = re.match(r"^([A-Z]+)\s+(.*?)(?:\s+HTTP/[\d.]+)?$", request_line)
    if not match:
        raise ValueError(f"无效的请求行: {request_line}")
    
    method, path = match.groups()
    
    headers = {}
    body = ""
    i = 1
    
    # 2. 解析 Headers
    while i < len(lines):
        line = lines[i]
        if line == "":
            # 空行，后面是 Body
            i += 1
            break
        
        if ":" in line:
            key, value = line.split(":", 1)
            headers[key.strip()] = value.strip()
        i += 1
        
    # 3. 解析 Body
    if i < len(lines):
        body = "\n".join(lines[i:])

    # 3.5 处理 target_host 替换
    if target_host:
        # 移除可能存在的不同大小写的 Host 头
        keys_to_remove = [k for k in headers.keys() if k.lower() == 'host']
        for k in keys_to_remove:
            del headers[k]
        headers["Host"] = target_host

        # 如果 path 是绝对 URI，也需要替换其中的 Host
        if path.lower().startswith("http"):
            from urllib.parse import urlparse, urlunparse
            parsed = urlparse(path)
            path = urlunparse(parsed._replace(netloc=target_host))
        
    # 4. 构造完整 URL
    if not path.lower().startswith("http"):
        host = headers.get("Host") or headers.get("host")
        if not host:
            raise ValueError("Raw request 中缺少 Host 头，无法构造完整 URL")
            
        # 智能识别 scheme: 如果没有明确指定 scheme 且 host 包含 :443，则默认为 https
        if scheme == "http" and ":443" in host:
            final_scheme = "https"
        else:
            final_scheme = scheme
            
        url = f"{final_scheme}://{host}{path}"
    else:
        url = path
        
    return method, url, headers, body

class RawHttpRequestSchema(BaseModel):
    raw_request: str = Field(
        ..., 
        description="原始 HTTP 请求报文，包含请求行、Headers 和 Body (通常从 Burp Suite 等工具复制)。\n示例:\nPOST /api/login HTTP/1.1\nHost: example.com\nContent-Type: application/json\n\n{\"username\": \"admin\"}"
    )
    scheme: str = Field(
        "http", 
        description="协议头 (http 或 https)。如果 Host 头包含 :443，会自动识别为 https。"
    )
    proxy: Optional[str] = Field(
        None, 
        description="代理地址，例如 http://127.0.0.1:8080。如果不填，将使用系统默认配置 (settings.SCAN_PROXY)。"
    )
    target_host: Optional[str] = Field(
        None,
        description="目标主机 (Host:Port)，例如 127.0.0.1:8000。如果指定，将强制替换请求中的 Host 头和目标地址。常用于流量重放。"
    )

@tool(args_schema=RawHttpRequestSchema)
async def send_raw_http_request(raw_request: str, scheme: str = "http", proxy: Optional[str] = None, target_host: Optional[str] = None) -> str:
    """
    解析并发送原始 HTTP 请求报文。
    适用于需要精确控制请求格式、测试特定 Payloads 或重放抓包数据的场景。
    """
    logger.info("正在解析并发送 Raw HTTP 请求...")
    
    # 使用系统配置的默认代理
    target_proxy = proxy or settings.SCAN_PROXY
    if target_proxy:
        logger.debug(f"使用代理: {target_proxy}")
    
    try:
        method, url, headers, body = parse_raw_request(raw_request, scheme, target_host)
        
        logger.info(f"发送请求: {method} {url}")
        
        # 过滤掉 httpx 会自动处理的 headers，避免冲突
        # 1. Host: httpx 会根据 URL 自动设置
        # 2. Content-Length: httpx 会根据 content 自动计算
        headers_to_send = {
            k: v for k, v in headers.items() 
            if k.lower() not in ["host", "content-length"]
        }
        
        # httpx 0.24+ 使用 proxy 参数 (单数)
        async with httpx.AsyncClient(proxy=target_proxy, verify=False, timeout=30.0) as client:
            response = await client.request(
                method=method,
                url=url,
                headers=headers_to_send,
                content=body.encode("utf-8") if body else None
            )
            
            result = f"Status Code: {response.status_code}\n"
            result += "Response Headers:\n"
            for k, v in response.headers.items():
                result += f"{k}: {v}\n"
            result += "\nResponse Body:\n"
            
            # 尝试解码响应体
            try:
                text = response.text
            except:
                text = "[Binary Content]"
                
            result += text[:1000] # 限制长度
            if len(text) > 1000:
                result += "\n...(truncated)..."
                
            return result
            
    except Exception as e:
        error_msg = f"请求发送失败: {str(e)}"
        logger.error(error_msg)
        return error_msg

class HttpRequestSchema(BaseModel):
    url: str = Field(..., description="目标 URL (e.g., https://api.example.com/v1/users)")
    method: str = Field("GET", description="HTTP 请求方法 (GET, POST, PUT, DELETE, etc.)")
    headers: Optional[Dict[str, str]] = Field(None, description="HTTP 请求头字典")
    body: Optional[str] = Field(None, description="HTTP 请求体内容 (字符串格式)")
    proxy: Optional[str] = Field(None, description="代理地址 (e.g., http://127.0.0.1:8080)。如果不填，将使用系统默认配置 (settings.SCAN_PROXY)。")

@tool(args_schema=HttpRequestSchema)
async def send_http_request(url: str, method: str = "GET", headers: Optional[Dict[str, str]] = None, body: Optional[str] = None, proxy: Optional[str] = None) -> str:
    """
    发送标准/结构化 HTTP 请求。
    适用于已知 URL、Method 等明确参数的场景，不需要手动拼接原始报文。
    """
    logger.info(f"发送结构化 HTTP 请求: {method} {url}")
    
    # 使用系统配置的默认代理
    target_proxy = proxy or settings.SCAN_PROXY
    if target_proxy:
        logger.debug(f"使用代理: {target_proxy}")
    
    try:
        async with httpx.AsyncClient(proxy=target_proxy, verify=False, timeout=30.0) as client:
            response = await client.request(
                method=method,
                url=url,
                headers=headers,
                content=body.encode("utf-8") if body else None
            )
            
            result = f"Status Code: {response.status_code}\n"
            result += "Response Headers:\n"
            for k, v in response.headers.items():
                result += f"{k}: {v}\n"
            result += "\nResponse Body:\n"
            
            try:
                text = response.text
            except:
                text = "[Binary Content]"
                
            result += text[:1000]
            if len(text) > 1000:
                result += "\n...(truncated)..."
                
            return result
            
    except Exception as e:
        error_msg = f"请求发送失败: {str(e)}"
        logger.error(error_msg)
        return error_msg
