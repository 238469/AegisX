from fastapi import APIRouter, HTTPException
from src.utils.db_helper import db_helper
from typing import List

router = APIRouter()

@router.get("/")
async def list_projects():
    """获取所有项目列表"""
    return db_helper.list_projects()

@router.delete("/{project_id}")
async def delete_project(project_id: int):
    """删除项目"""
    try:
        db_helper.delete_project(project_id)
        return {"status": "success", "message": "项目已删除"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{project_name}/vulnerabilities")
async def get_project_vulnerabilities(project_name: str):
    """获取指定项目的漏洞列表"""
    return db_helper.query_vulnerabilities_by_project(project_name)

@router.get("/{project_name}/logs")
async def get_project_logs(project_name: str):
    """获取指定项目的 Agent 交互日志"""
    return db_helper.query_logs_by_project(project_name)
