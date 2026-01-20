import json
import time
from datetime import datetime
from pathlib import Path
from loguru import logger

class LLMAuditor:
    """
    LLM 交互审计记录器
    """
    def __init__(self, log_dir: str = "logs/llm_audit"):
        self.log_path = Path(log_dir)
        self.log_path.mkdir(parents=True, exist_ok=True)

    def record(self, agent_name: str, task_id: str, prompt: any, response: any, project_name: str = "Default"):
        """记录单次交互"""
        
        entry = {
            "timestamp": datetime.now().isoformat(),
            "project": project_name,
            "agent": agent_name,
            "task_id": task_id,
            "prompt": str(prompt),
            "response": str(response)
        }
        
        # 1. 写入 JSONL 文件 (已禁用，仅写入数据库)
        # try:
        #     with open(log_file, "a", encoding="utf-8") as f:
        #         f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        # except Exception as e:
        #     logger.error(f"无法写入 LLM 审计日志文件: {e}")

        # 2. 写入 SQLite 数据库 (新增)
        try:
            from src.utils.db_helper import db_helper
            db_helper.save_agent_log(project_name, entry)
        except Exception as e:
            logger.error(f"无法将 LLM 审计日志存入数据库: {e}")

auditor = LLMAuditor()
