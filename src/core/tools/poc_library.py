import httpx
from bs4 import BeautifulSoup
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from loguru import logger
import asyncio
from typing import List, Optional

class PocLibrarySearchSchema(BaseModel):
    keyword: str = Field(..., description="搜索关键词，例如 '泛微', 'Spring', 'ThinkPHP'")
    max_results: int = Field(10, description="最大返回的 POC 数量，默认为 10")

@tool(args_schema=PocLibrarySearchSchema)
async def search_poc_library(keyword: str, max_results: int = 10) -> str:
    """
    从漏洞情报库 (biu.life) 搜索并提取包含实战 POC 代码的漏洞详情。
    
    特点:
    1. 仅筛选带有 "POC" 标签的高价值漏洞。
    2. 自动进入详情页抓取具体的 POC/Exp 代码片段。
    3. 返回格式化的漏洞描述和代码，可直接用于漏洞验证。
    """
    base_url = "https://rss.biu.life"
    search_url = f"{base_url}/ti/search"
    
    logger.info(f"正在 POC 库中搜索: {keyword}")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    results = []
    
    try:
        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            # 1. 搜索列表页
            try:
                resp = await client.get(search_url, params={"q": keyword}, headers=headers)
                resp.raise_for_status()
            except Exception as e:
                return f"搜索请求失败: {str(e)}"

            soup = BeautifulSoup(resp.text, 'html.parser')
            items = soup.find_all('li', class_='poc-item')
            
            logger.info(f"找到 {len(items)} 个相关条目，正在筛选 POC...")
            
            tasks = []
            valid_items = []

            # 2. 筛选带有 POC 标签的条目
            for item in items:
                if len(valid_items) >= max_results:
                    break
                    
                poc_tag = item.find('span', class_='poc-tag poc-exists')
                if poc_tag:
                    link_tag = item.find('a')
                    if not link_tag:
                        continue
                        
                    title = link_tag.get_text(strip=True)
                    # 清理标题中的日期 (e.g., "2021-01-19泛微...")
                    date_span = link_tag.find('span', class_='datetime')
                    if date_span:
                        date_text = date_span.get_text(strip=True)
                        title = title.replace(date_text, "").strip()
                        
                    href = link_tag['href']
                    full_url = base_url + href if href.startswith('/') else href
                    
                    valid_items.append({
                        "title": title,
                        "url": full_url
                    })

            if not valid_items:
                return f"未找到关于 '{keyword}' 且包含 POC 代码的漏洞条目。"

            # 3. 并发获取详情页 POC 代码
            for item in valid_items:
                tasks.append(_fetch_poc_detail(client, item["url"], item["title"]))
            
            # 等待所有详情页抓取完成
            details = await asyncio.gather(*tasks)
            results.extend(details)

    except Exception as e:
        logger.error(f"POC 搜索过程中发生错误: {e}")
        return f"执行过程中发生错误: {str(e)}"

    # 4. 格式化输出
    output = f"🔍 搜索关键词: {keyword}\n"
    output += f"🎯 找到 {len(results)} 个包含 POC 的漏洞:\n\n"
    output += "\n".join(results)
    
    return output

async def _fetch_poc_detail(client: httpx.AsyncClient, url: str, title: str) -> str:
    """辅助函数：抓取单个页面的 POC 代码"""
    try:
        resp = await client.get(url)
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        code_blocks = soup.find_all('code')
        poc_content = ""
        
        if code_blocks:
            for i, code in enumerate(code_blocks):
                text = code.get_text().strip()
                if text and text != "暂无":
                    # 截断过长的代码，避免 Token 溢出，但保留足够长度
                    if len(text) > 2000:
                        text = text[:2000] + "\n...(代码过长已截断)..."
                    poc_content += f"\n💻 POC 代码片段 {i+1}:\n```\n{text}\n```\n"
        
        if not poc_content:
            poc_content = "\n(未检测到标准格式的代码块，请访问链接查看)\n"

        return (
            f"🔴 **{title}**\n"
            f"🔗 链接: {url}\n"
            f"{poc_content}"
            f"{'-'*40}"
        )
    except Exception as e:
        return f"🔴 **{title}**\n🔗 {url}\n❌ 获取详情失败: {str(e)}\n{'-'*40}"
