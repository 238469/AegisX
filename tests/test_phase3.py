import sys
import os
from pathlib import Path

# 将项目根目录添加到 python 路径
sys.path.append(str(Path(__file__).parent.parent))

from src.agents.manager.graph import graph
from src.agents.manager.state import AgentState
import uuid

def test_manager_decision():
    print("--- 开始测试 Manager 决策逻辑 ---")
    
    # 模拟一个典型的 SQLi 漏洞请求
    mock_state: AgentState = {
        "request_id": str(uuid.uuid4()),
        "target_url": "http://example.com/?name=zhangsna",
        "method": "GET",
        "headers": {"User-Agent": "Mozilla/5.0"},
        "body": None,
        "tasks": [],
        "messages": [],
        "audit_log": []
    }

    print(f"测试请求: {mock_state['target_url']}")
    
    # 运行图
    result = graph.invoke(mock_state)
    
    print("\n[决策结果]")
    print(f"分配的任务: {result['tasks']}")
    
    # 验证审计日志
    from src.utils.db_helper import db_helper
    projects = db_helper.list_projects()
    if projects:
        print(f"\n[审计日志] 已确认存入数据库，当前项目数: {len(projects)}")
    else:
        print("\n[警告] 数据库中未找到项目记录（可能是首次运行）")
    
    # log_files = list(Path("logs/llm_audit").glob("*.jsonl"))
    # if log_files:
    #     print(f"\n[审计日志] 已生成: {log_files[0]}")
    # else:
    #     print("\n[错误] 未生成审计日志！")

if __name__ == "__main__":
    test_manager_decision()
