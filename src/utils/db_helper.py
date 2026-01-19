import sqlite3
import json
import os
from datetime import datetime
from pathlib import Path
from loguru import logger
from typing import List, Dict, Any, Optional

class DBHelper:
    """
    SQLite 数据库助手，负责漏洞结果和 Agent 日志的持久化
    """
    def __init__(self, db_path: str = "data/webagent.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        """初始化数据库表结构"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # 1. 项目表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 2. 漏洞结果表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS vulnerabilities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER NOT NULL,
                    request_id TEXT NOT NULL,
                    vuln_type TEXT NOT NULL,
                    url TEXT NOT NULL,
                    method TEXT,
                    parameter TEXT,
                    payload TEXT,
                    evidence TEXT,
                    full_request TEXT,
                    severity TEXT DEFAULT 'high',
                    found_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (project_id) REFERENCES projects (id)
                )
            ''')
            
            # 自动迁移：检查 full_request 列是否存在，不存在则添加
            cursor.execute("PRAGMA table_info(vulnerabilities)")
            columns = [column[1] for column in cursor.fetchall()]
            if 'full_request' not in columns:
                cursor.execute("ALTER TABLE vulnerabilities ADD COLUMN full_request TEXT")
                logger.info("数据库迁移：在 vulnerabilities 表中添加了 full_request 列")
            
            # 3. Agent 日志表 (LLM 审计日志)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS agent_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER NOT NULL,
                    request_id TEXT NOT NULL,
                    agent_name TEXT NOT NULL,
                    prompt TEXT,
                    response TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (project_id) REFERENCES projects (id)
                )
            ''')
            
            conn.commit()
            logger.info(f"数据库初始化完成: {self.db_path}")

    def get_or_create_project(self, name: str) -> int:
        """获取或创建项目，返回项目 ID"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM projects WHERE name = ?', (name,))
            row = cursor.fetchone()
            if row:
                return row[0]
            
            cursor.execute('INSERT INTO projects (name) VALUES (?)', (name,))
            conn.commit()
            return cursor.lastrowid

    def save_vulnerability(self, project_name: str, vuln_data: Dict[str, Any]):
        """保存漏洞结果"""
        project_id = self.get_or_create_project(project_name)
        
        # 处理 full_request，如果是 dict 则转为 JSON 字符串
        full_request = vuln_data.get("full_request")
        if isinstance(full_request, dict):
            full_request = json.dumps(full_request, ensure_ascii=False)
            
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO vulnerabilities (
                    project_id, request_id, vuln_type, url, method, 
                    parameter, payload, evidence, full_request, severity
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                project_id,
                vuln_data.get("request_id"),
                vuln_data.get("type"),
                vuln_data.get("url"),
                vuln_data.get("method"),
                vuln_data.get("parameter"),
                vuln_data.get("payload"),
                vuln_data.get("evidence"),
                full_request,
                vuln_data.get("severity", "high")
            ))
            conn.commit()

    def save_agent_log(self, project_name: str, log_data: Dict[str, Any]):
        """保存 Agent 日志"""
        # 如果没有项目名称，记录到 Default 项目
        project_id = self.get_or_create_project(project_name or "Default")
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO agent_logs (
                    project_id, request_id, agent_name, prompt, response
                ) VALUES (?, ?, ?, ?, ?)
            ''', (
                project_id,
                log_data.get("task_id"),
                log_data.get("agent"),
                log_data.get("prompt"),
                log_data.get("response")
            ))
            conn.commit()

    def query_vulnerabilities_by_project(self, project_name: str) -> List[Dict]:
        """按项目查询漏洞"""
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT v.* FROM vulnerabilities v
                JOIN projects p ON v.project_id = p.id
                WHERE p.name = ?
                ORDER BY v.found_at DESC
            ''', (project_name,))
            return [dict(row) for row in cursor.fetchall()]

    def query_logs_by_project(self, project_name: str) -> List[Dict]:
        """按项目查询 Agent 日志处理"""
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT l.* FROM agent_logs l
                JOIN projects p ON l.project_id = p.id
                WHERE p.name = ?
                ORDER BY l.timestamp DESC
            ''', (project_name,))
            return [dict(row) for row in cursor.fetchall()]

    def get_session_summary(self) -> str:
        """获取本次会话的汇总信息（用于程序关闭时打印）"""
        summary = []
        summary.append("\n" + "="*50)
        summary.append("      WebAgent 运行汇总报告 (Shutdown Summary)")
        summary.append("="*50)
        
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # 1. 统计各项目情况
            cursor.execute('''
                SELECT p.name, 
                       (SELECT COUNT(*) FROM vulnerabilities v WHERE v.project_id = p.id) as vuln_count,
                       (SELECT COUNT(*) FROM agent_logs l WHERE l.project_id = p.id) as log_count
                FROM projects p
            ''')
            projects = cursor.fetchall()
            
            if not projects:
                summary.append("暂无项目数据记录。")
                return "\n".join(summary)

            for p in projects:
                summary.append(f"\n[ 项目: {p['name']} ]")
                summary.append(f"  - 发现漏洞总数: {p['vuln_count']}")
                summary.append(f"  - Agent 交互次数: {p['log_count']}")
                
                # 2. 列出该项目的漏洞简报
                if p['vuln_count'] > 0:
                    summary.append("  - 漏洞列表:")
                    cursor.execute('SELECT vuln_type, parameter, url FROM vulnerabilities WHERE project_id = (SELECT id FROM projects WHERE name = ?)', (p['name'],))
                    vulns = cursor.fetchall()
                    for v in vulns:
                        summary.append(f"    * [{v['vuln_type']}] 参数: {v['parameter']} -> {v['url'][:60]}...")
                
                # 3. 列出该项目的对话摘要 (最近 5 条)
                if p['log_count'] > 0:
                    summary.append("  - Agent 对话摘要 (最近 5 条):")
                    cursor.execute('SELECT agent_name, timestamp FROM agent_logs WHERE project_id = (SELECT id FROM projects WHERE name = ?) ORDER BY timestamp DESC LIMIT 5', (p['name'],))
                    logs = cursor.fetchall()
                    for l in logs:
                        summary.append(f"    * [{l['timestamp']}] {l['agent_name']}")
            
        summary.append("\n" + "="*50)
        return "\n".join(summary)

# 单例模式
db_helper = DBHelper()
