modules = [
    "src.core.tools.http_sender",
    "src.core.tools.code_interpreter",
    "src.core.tools.web_search",
    "src.core.tools.poc_library",
    "src.core.tools.ceye_verify"
]

for module in modules:
    try:
        __import__(module)
        print(f"✅ {module.split('.')[-1]} loaded")
    except Exception as e:
        print(f"❌ {module.split('.')[-1]} failed: {e}")
