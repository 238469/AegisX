import asyncio
import json
import sqlite3
import os
from pathlib import Path
from src.utils.db_helper import db_helper
from src.utils.auditor import auditor

async def test_db_persistence():
    project_name = "Test_Project_2026"
    request_id = "test-req-123"
    
    print(f"--- 1. 测试项目创建与日志持久化 ---")
    # 模拟审计日志记录
    auditor.record(
        agent_name="Test_Agent",
        task_id=request_id,
        prompt="Hello AI",
        response="Hello Human",
        project_name=project_name
    )
    
    # 验证日志是否入库
    logs = db_helper.query_logs_by_project(project_name)
    print(f"项目 '{project_name}' 的日志条数: {len(logs)}")
    if len(logs) > 0:
        print(f"最新日志内容: {logs[0]['prompt']} -> {logs[0]['response']}")
        print("✅ 日志持久化验证成功")
    else:
        print("❌ 日志持久化验证失败")
        return

    print(f"\n--- 2. 测试漏洞结果持久化 ---")
    finding = {
        "request_id": request_id,
        "type": "SQL Injection",
        "url": "http://example.com/login",
        "method": "POST",
        "parameter": "username",
        "payload": "' OR 1=1 --",
        "evidence": "Detected time delay of 5s",
        "severity": "high",
        "full_request": {
            "method": "POST",
            "url": "http://example.com/login",
            "headers": {"Content-Type": "application/x-www-form-urlencoded"},
            "body": "username=admin&password=123"
        }
    }
    db_helper.save_vulnerability(project_name, finding)
    
    # 验证漏洞是否入库
    vulns = db_helper.query_vulnerabilities_by_project(project_name)
    print(f"项目 '{project_name}' 的漏洞条数: {len(vulns)}")
    if len(vulns) > 0:
        print(f"漏洞详情: {vulns[0]['vuln_type']} at {vulns[0]['parameter']}")
        print(f"原始请求包内容: {vulns[0]['full_request']}")
        if "username=admin" in vulns[0]['full_request']:
            print("✅ 原始请求包持久化验证成功")
        else:
            print("❌ 原始请求包持久化验证失败")
    else:
        print("❌ 漏洞持久化验证失败")
        return

    print(f"\n--- 3. 验证数据库结构 ---")
    with sqlite3.connect("data/webagent.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"数据库中的表: {tables}")
        
    print("\n--- 所有数据库测试通过 ---")

if __name__ == "__main__":
    asyncio.run(test_db_persistence())
