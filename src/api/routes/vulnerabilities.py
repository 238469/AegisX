from fastapi import APIRouter
from src.utils.db_helper import db_helper

router = APIRouter()

@router.get("/")
async def list_all_vulnerabilities():
    """获取所有发现的漏洞列表"""
    return db_helper.query_all_vulnerabilities()
