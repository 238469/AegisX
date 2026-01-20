from typing import Optional, List, Dict, Any
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from loguru import logger
from ddgs import DDGS
import httpx
from bs4 import BeautifulSoup
import re

from src.config.settings import settings

class SearchInput(BaseModel):
    query: str = Field(..., description="要搜索的关键词或问题")
    max_results: int = Field(5, description="返回的最大结果数量 (默认为 5)")
    region: str = Field("wt-wt", description="搜索地区代码 (例如 'wt-wt' 表示全球, 'cn-zh' 表示中国)")

class ExploitSearchInput(BaseModel):
    query: str = Field(..., description="漏洞名称或 CVE 编号 (例如 'ThinkPHP 5 RCE', 'CVE-2019-11043')")
    max_results: int = Field(5, description="返回的最大结果数量 (默认为 5)")

class WebContentInput(BaseModel):
    url: str = Field(..., description="要获取内容的网页 URL")

@tool(args_schema=SearchInput)
async def web_search(query: str, max_results: int = 5, region: str = "wt-wt") -> str:
    """
    使用 DuckDuckGo 进行网络搜索。
    适用于获取实时信息、查找技术文档、解决编程问题或获取最新新闻。
    """
    return await _perform_search(query, max_results, region)

@tool(args_schema=ExploitSearchInput)
async def search_exploits(query: str, max_results: int = 5) -> str:
    """
    专注于搜索安全漏洞 POC 和 Exploit 代码。
    优先使用 GitHub API 搜索，如果失败则回退到通用搜索。
    """
    logger.info(f"执行 Exploit 搜索: {query}")
    
    # 1. 优先尝试 GitHub API 搜索 (更稳定，针对代码)
    try:
        github_results = await _search_github(query, max_results)
        if github_results:
            return github_results
    except Exception as e:
        logger.warning(f"GitHub 搜索失败: {e}")
    
    # 2. 如果 GitHub 没找到或失败，回退到 DuckDuckGo
    logger.info("GitHub 搜索无结果或失败，回退到通用搜索...")
    dork_query = f"{query} POC exploit github"
    return await _perform_search(dork_query, max_results, region="wt-wt")

async def _search_github(query: str, max_results: int) -> Optional[str]:
    """
    使用 GitHub Search API 搜索代码仓库
    """
    api_url = "https://api.github.com/search/repositories"
    # 添加 'poc' 或 'exploit' 关键词以提高准确性
    search_q = f"{query} poc OR {query} exploit"
    params = {
        "q": search_q,
        "sort": "stars",
        "order": "desc",
        "per_page": max_results
    }
    
    async with httpx.AsyncClient(verify=False, proxy=settings.SCAN_PROXY, timeout=10.0) as client:
        resp = await client.get(api_url, params=params)
        
        if resp.status_code == 200:
            data = resp.json()
            items = data.get("items", [])
            if not items:
                return None
                
            formatted = f"🐙 GitHub 搜索结果 ('{search_q}'):\n\n"
            for i, item in enumerate(items, 1):
                name = item.get("full_name")
                url = item.get("html_url")
                desc = item.get("description") or "No description"
                stars = item.get("stargazers_count")
                updated = item.get("updated_at")
                
                formatted += f"{i}. {name} (⭐ {stars})\n"
                formatted += f"   🔗 {url}\n"
                formatted += f"   📝 {desc}\n"
                formatted += f"   🕒 Updated: {updated}\n\n"
            return formatted
            
        elif resp.status_code == 403:
            logger.warning("GitHub API Rate Limit Exceeded")
            return None
        else:
            logger.warning(f"GitHub API Error: {resp.status_code}")
            return None

@tool(args_schema=WebContentInput)
async def fetch_web_content(url: str) -> str:
    """
    获取指定 URL 的网页内容（文本和代码）。
    适用于读取 GitHub 代码文件、技术博客文章或漏洞详情页。
    """
    logger.info(f"正在获取网页内容: {url}")
    try:
        # 处理 GitHub Blob URL -> Raw URL
        # e.g. https://github.com/user/repo/blob/main/file.py -> https://raw.githubusercontent.com/user/repo/main/file.py
        if "github.com" in url and "/blob/" in url:
            raw_url = url.replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")
            logger.info(f"检测到 GitHub Blob URL，转换为 Raw URL: {raw_url}")
            url = raw_url

        # 第一次尝试：使用代理
        try:
            async with httpx.AsyncClient(verify=False, proxy=settings.SCAN_PROXY, follow_redirects=True, timeout=20.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                return _parse_response(response, url)
        except Exception as e:
            logger.warning(f"使用代理获取网页内容失败: {e}")
            if settings.SCAN_PROXY:
                logger.info("尝试直接连接 (不使用代理)...")
                # 第二次尝试：直连
                async with httpx.AsyncClient(verify=False, follow_redirects=True, timeout=20.0) as client:
                    response = await client.get(url)
                    response.raise_for_status()
                    return _parse_response(response, url)
            else:
                raise e

    except Exception as e:
        logger.error(f"获取网页内容失败: {e}")
        return f"获取网页内容失败: {e}"

def _parse_response(response: httpx.Response, url: str) -> str:
    content_type = response.headers.get("content-type", "")
    
    # 如果是纯文本或代码 (GitHub Raw)
    if "text/plain" in content_type or "application/json" in content_type or "raw.githubusercontent.com" in url:
        return f"📄 原始内容 ({url}):\n\n{response.text[:10000]}" # 限制返回长度

    # 如果是 HTML，提取正文
    soup = BeautifulSoup(response.text, "html.parser")
    
    # 移除脚本和样式
    for script in soup(["script", "style", "nav", "footer", "header"]):
        script.decompose()
        
    # 提取文本
    text = soup.get_text(separator="\n")
    
    # 清理空行
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    clean_text = '\n'.join(chunk for chunk in chunks if chunk)
    
    return f"📄 网页内容 ({url}):\n\n{clean_text[:8000]}..." # 限制返回长度

async def _perform_search(query: str, max_results: int, region: str) -> str:
    logger.info(f"正在执行网络搜索: {query} (max={max_results}, region={region})")
    try:
        results = []
        # 优先使用环境变量中的代理，或者 settings 配置
        # 如果连接失败，可以尝试不使用代理
        proxy = settings.SCAN_PROXY
        
        # 第一次尝试
        try:
            with DDGS(proxy=proxy, timeout=20, verify=False) as ddgs:
                # ddgs 9.10.0+ requires positional 'query' not 'keywords' for text()
                # 兼容性处理
                try:
                    ddgs_gen = ddgs.text(query, region=region, max_results=max_results)
                except TypeError:
                    # Fallback for older versions
                    ddgs_gen = ddgs.text(keywords=query, region=region, max_results=max_results)
                    
                for r in ddgs_gen:
                    results.append(r)
        except Exception as e:
            logger.warning(f"第一次搜索尝试失败 (proxy={proxy}): {e}")
            # 如果配置了代理但失败了，尝试直连 (可能代理不稳定)
            if proxy:
                logger.info("尝试直接连接 (不使用代理)...")
                with DDGS(timeout=20, verify=False) as ddgs:
                    try:
                        ddgs_gen = ddgs.text(query, region=region, max_results=max_results)
                    except TypeError:
                        ddgs_gen = ddgs.text(keywords=query, region=region, max_results=max_results)
                        
                    for r in ddgs_gen:
                        results.append(r)
            else:
                raise e
        
        if not results:
            return "未找到相关结果。"
            
        formatted_results = f"🔍 搜索结果 ('{query}'):\n\n"
        for i, res in enumerate(results, 1):
            title = res.get('title', 'No Title')
            link = res.get('href', '#')
            snippet = res.get('body', 'No description available.')
            
            formatted_results += f"{i}. {title}\n"
            formatted_results += f"   🔗 {link}\n"
            formatted_results += f"   📝 {snippet}\n\n"
            
        return formatted_results.strip()

    except Exception as e:
        error_msg = f"搜索失败: {str(e)}"
        logger.error(error_msg)
        return error_msg
