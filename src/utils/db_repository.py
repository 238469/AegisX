import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from loguru import logger

class DBRepository:
    """
    数据库仓库类，封装所有 SQL 操作
    """
    def __init__(self, connection_factory):
        self._get_connection = connection_factory

    def init_tables(self):
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
            
            # 自动迁移：检查 full_request 列是否存在
            cursor.execute("PRAGMA table_info(vulnerabilities)")
            columns = [column[1] for column in cursor.fetchall()]
            if 'full_request' not in columns:
                cursor.execute("ALTER TABLE vulnerabilities ADD COLUMN full_request TEXT")
                logger.info("数据库迁移：在 vulnerabilities 表中添加了 full_request 列")
            
            # 3. Agent 日志表
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

    def get_or_create_project(self, name: str) -> int:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM projects WHERE name = ?', (name,))
            row = cursor.fetchone()
            if row:
                return row[0]
            
            cursor.execute('INSERT INTO projects (name) VALUES (?)', (name,))
            conn.commit()
            return cursor.lastrowid

    def list_projects(self) -> List[Dict]:
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT p.*, 
                       (SELECT COUNT(*) FROM vulnerabilities v WHERE v.project_id = p.id) as vuln_count,
                       (SELECT COUNT(*) FROM agent_logs l WHERE l.project_id = p.id) as log_count
                FROM projects p
                ORDER BY created_at DESC
            ''')
            return [dict(row) for row in cursor.fetchall()]

    def delete_project(self, project_id: int):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA foreign_keys = ON")
            cursor.execute('DELETE FROM agent_logs WHERE project_id = ?', (project_id,))
            cursor.execute('DELETE FROM vulnerabilities WHERE project_id = ?', (project_id,))
            cursor.execute('DELETE FROM projects WHERE id = ?', (project_id,))
            conn.commit()

    def save_vulnerability(self, project_id: int, vuln_data: Dict[str, Any]):
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

    def save_agent_log(self, project_id: int, log_data: Dict[str, Any]):
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

    def query_vulnerabilities(self, project_id: Optional[int] = None) -> List[Dict]:
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            if project_id:
                cursor.execute('''
                    SELECT v.*, p.name as project_name FROM vulnerabilities v
                    JOIN projects p ON v.project_id = p.id
                    WHERE v.project_id = ?
                    ORDER BY v.found_at DESC
                ''', (project_id,))
            else:
                cursor.execute('''
                    SELECT v.*, p.name as project_name FROM vulnerabilities v
                    JOIN projects p ON v.project_id = p.id
                    ORDER BY v.found_at DESC
                ''')
            return [dict(row) for row in cursor.fetchall()]

    def query_logs(self, project_id: int) -> List[Dict]:
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT l.* FROM agent_logs l
                WHERE l.project_id = ?
                ORDER BY l.timestamp DESC
            ''', (project_id,))
            return [dict(row) for row in cursor.fetchall()]
