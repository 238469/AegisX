import sys
from pathlib import Path

# 确保项目根目录在 sys.path 中，以便可以正确导入 src 模块
sys.path.append(str(Path(__file__).resolve().parents[2]))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.routes import settings, projects, vulnerabilities, scanner
from src.config.settings import settings as app_settings
from src.utils.logger_config import setup_logging
from src.core.engine.manager import scanner_manager

# 初始化全局日志
setup_logging()

app = FastAPI(title="AegisX API", version="1.0.0")

@app.on_event("shutdown")
def shutdown_event():
    # 退出时确保所有子进程都已关闭
    scanner_manager.stop_all()

# 配置跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(settings.router, prefix="/api/settings", tags=["Settings"])
app.include_router(projects.router, prefix="/api/projects", tags=["Projects"])
app.include_router(vulnerabilities.router, prefix="/api/vulnerabilities", tags=["Vulnerabilities"])
app.include_router(scanner.router, prefix="/api/scanner", tags=["Scanner"])

@app.get("/")
async def root():
    return {"message": "AegisX API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
