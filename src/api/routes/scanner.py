from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from src.utils.redis_helper import RedisHelper
from src.core.engine.manager import scanner_manager
import asyncio
import json
from loguru import logger

router = APIRouter()
redis = RedisHelper()

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                pass

manager = ConnectionManager()

@router.get("/status")
async def get_status():
    """获取扫描器状态"""
    manager_status = scanner_manager.get_status()
    return {
        "status": "running" if any(v == "running" for v in manager_status.values()) else "idle",
        "components": manager_status
    }

@router.post("/start")
async def start_scanner(project_name: str = "Default"):
    """开始扫描 (设置当前活跃项目并确保组件启动)"""
    # 1. 设置当前活跃项目
    redis.client.set("webagent:current_project", project_name)
    
    # 2. 启动/确保拦截器和执行器运行
    scanner_manager.start_components()
    
    return {"status": "success", "message": f"项目 {project_name} 扫描已启动"}

@router.post("/stop")
async def stop_scanner():
    """停止扫描组件"""
    scanner_manager.stop_all()
    return {"status": "success", "message": "扫描组件已停止"}

@router.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket):
    await manager.connect(websocket)
    pubsub = redis.client.pubsub()
    pubsub.subscribe("webagent:logs")
    
    try:
        while True:
            # 检查 pubsub 消息
            message = pubsub.get_message(ignore_subscribe_messages=True)
            if message:
                log_data = message['data']
                if isinstance(log_data, bytes):
                    log_data = log_data.decode('utf-8')
                await websocket.send_text(log_data)
            await asyncio.sleep(0.1)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket 异常: {e}")
        manager.disconnect(websocket)
    finally:
        pubsub.unsubscribe("webagent:logs")
