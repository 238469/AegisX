import asyncio
import sys
from pathlib import Path

# Add project root
sys.path.append(str(Path(__file__).parent.parent))

from src.core.tools.web_search import web_search

async def test_search():
    # Test 2: Chinese Search
    query_cn = "泛微OA POC"
    print(f"\nSearching for (CN): {query_cn}...")
    
    result_cn = await web_search.ainvoke({"query": query_cn, "max_results": 3, "region": "cn-zh"})
    print(f"Result (CN):\n{result_cn}")

if __name__ == "__main__":
    asyncio.run(test_search())
