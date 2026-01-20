import requests
import sys
import urllib3
from loguru import logger

# 禁用不安全请求警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 配置日志
logger.remove()
logger.add(sys.stderr, format="<green>{time:HH:mm:ss}</green> | <level>{message}</level>")

# 配置代理 (指向 mitmproxy 端口，默认 8080)
PROXIES = {
    "http": "http://127.0.0.1:8080",
    "https": "http://127.0.0.1:8080",
}

# 目标 URL (这里使用本地 Pikachu 靶场的 SQL 注入题目作为示例)
# 如果没有 Pikachu，可以使用 httpbin.org: "http://httpbin.org/get?id=1&name=test"
TARGET_URL = "http://127.0.0.1/pikachu-master/vul/sqli/sqli_str.php?name=1&submit=%E6%9F%A5%E8%AF%A2"

def send_test_traffic():
    """
    发送测试流量经过 Proxy，触发后端扫描分析
    """
    logger.info(f"🚀 正在发送测试流量...")
    logger.info(f"📍 目标: {TARGET_URL}")
    logger.info(f"🔌 代理: {PROXIES['http']}")

    try:
        # 发送 GET 请求
        response = requests.get(
            TARGET_URL, 
            proxies=PROXIES, 
            verify=False,  # 忽略 mitmproxy 自签名证书警告
            timeout=10
        )
        
        logger.info(f"✅ 请求发送成功")
        logger.info(f"📊 状态码: {response.status_code}")
        logger.info(f"📄 响应长度: {len(response.text)} 字符")
        
        if response.status_code == 200:
            logger.success("流量应已被 mitmproxy 捕获并推送到扫描引擎。请观察后端日志或前端控制台。")
        else:
            logger.warning(f"响应状态码非 200，请检查目标服务状态。")

    except requests.exceptions.ProxyError:
        logger.error("❌ 连接代理失败。请确保 main.py 已启动且 mitmproxy 正在运行 (端口 8080)。")
    except requests.exceptions.ConnectionError:
        logger.error("❌ 连接目标服务失败。请确保目标 URL 可访问。")
    except Exception as e:
        logger.error(f"❌ 发生未知错误: {e}")

if __name__ == "__main__":
    send_test_traffic()
