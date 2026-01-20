import sqlite3
import os
from pathlib import Path
from loguru import logger
from typing import List, Dict, Any, Optional
from .db_repository import DBRepository

class DBHelper:
    """
    SQLite 数据库助手，负责连接管理，并持有 DBRepository 进行实际操作
    """
    def __init__(self, db_path: str = None):
        if db_path is None:
            # 默认指向项目根目录下的 data/webagent.db
            base_dir = Path(__file__).resolve().parent.parent.parent
            self.db_path = base_dir / "data" / "webagent.db"
        else:
            self.db_path = Path(db_path)
        
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.repo = DBRepository(self._get_connection)
        self._init_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        """初始化数据库"""
        try:
            self.repo.init_tables()
            logger.info(f"数据库初始化完成: {self.db_path}")
        except Exception as e:
            logger.error(f"数据库初始化失败: {e}")

    # --- 代理方法，调用 repo ---
    
    def get_or_create_project(self, name: str) -> int:
        return self.repo.get_or_create_project(name)

    def save_vulnerability(self, project_name: str, vuln_data: Dict[str, Any]):
        project_id = self.get_or_create_project(project_name)
        self.repo.save_vulnerability(project_id, vuln_data)

    def save_agent_log(self, project_name: str, log_data: Dict[str, Any]):
        project_id = self.get_or_create_project(project_name or "Default")
        self.repo.save_agent_log(project_id, log_data)

    def query_vulnerabilities_by_project(self, project_name: str) -> List[Dict]:
        project_id = self.get_or_create_project(project_name)
        return self.repo.query_vulnerabilities(project_id)

    def query_logs_by_project(self, project_name: str) -> List[Dict]:
        project_id = self.get_or_create_project(project_name)
        return self.repo.query_logs(project_id)

    def list_projects(self) -> List[Dict]:
        return self.repo.list_projects()

    def delete_project(self, project_id: int):
        self.repo.delete_project(project_id)

    def query_all_vulnerabilities(self) -> List[Dict]:
        return self.repo.query_vulnerabilities()

    def get_session_summary(self) -> str:
        """获取汇总信息（保持原有逻辑用于打印）"""
        summary = []
        summary.append("\n" + "="*50)
        summary.append("      WebAgent 运行汇总报告 (Shutdown Summary)")
        summary.append("="*50)
        
        projects = self.list_projects()
        if not projects:
            summary.append("暂无项目数据记录。")
            return "\n".join(summary)

        for p in projects:
            summary.append(f"\n[ 项目: {p['name']} ]")
            summary.append(f"  - 发现漏洞总数: {p['vuln_count']}")
            summary.append(f"  - Agent 交互次数: {p['log_count']}")
            
            if p['vuln_count'] > 0:
                summary.append("  - 漏洞列表:")
                vulns = self.repo.query_vulnerabilities(p['id'])
                for v in vulns:
                    summary.append(f"    * [{v['vuln_type']}] {v['url']} (Param: {v['parameter']})")
        
        return "\n".join(summary)

# 全局单例
db_helper = DBHelper()
