import asyncio
import sys
from pathlib import Path

# Add project root
sys.path.append(str(Path(__file__).parent.parent))

from src.core.tools.web_search import search_exploits, fetch_web_content

async def test_poc_search():
    print("--- Testing Exploit Search Tool ---")
    
    # Test 1: Search for a known CVE POC
    # Using a slightly older one to ensure results
    query = "CVE-2022-22965 Spring4Shell" 
    print(f"\nSearching for POC: {query}...")
    
    try:
        result = await search_exploits.ainvoke({"query": query, "max_results": 3})
        print(f"Result:\n{result}")
        
        # Parse result to find a URL to fetch (Naive parsing for test)
        import re
        urls = re.findall(r'🔗 (https?://[^\s]+)', result)
        if urls:
            target_url = urls[0]
            print(f"\n--- Testing Web Content Fetcher ---")
            print(f"Fetching content from: {target_url}")
            
            content = await fetch_web_content.ainvoke({"url": target_url})
            print(f"Content Preview (first 500 chars):\n{content[:500]}")
            
        else:
            print("\n⚠️ No URLs found in search results to test fetcher.")

    except Exception as e:
        print(f"Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_poc_search())
