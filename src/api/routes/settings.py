from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from src.config.settings import settings, Settings
import os
from dotenv import set_key
from typing import Dict, Any

router = APIRouter()

class SettingsUpdate(BaseModel):
    configs: Dict[str, Any]

@router.get("/")
async def get_settings():
    """获取当前系统配置"""
    # 过滤掉敏感信息或只返回必要的配置
    return settings.model_dump()

@router.post("/")
async def update_settings(update: SettingsUpdate):
    """更新系统配置并持久化到 .env"""
    env_path = ".env"
    if not os.path.exists(env_path):
        with open(env_path, "w") as f:
            f.write("")

    try:
        for key, value in update.configs.items():
            # 校验 key 是否在 Settings 中
            if hasattr(settings, key):
                # 更新内存中的配置
                setattr(settings, key, value)
                # 持久化到 .env
                set_key(env_path, key, str(value))
        
        return {"status": "success", "message": "配置已更新"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新配置失败: {str(e)}")
