import os
import subprocess
import signal
import sys
import time
import asyncio
from typing import Optional
from loguru import logger
from src.config.settings import settings

class ScannerManager:
    """
    扫描器管理器：负责控制 mitmproxy 和 TaskRunner 的生命周期
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ScannerManager, cls).__new__(cls)
            cls._instance.p_mitm = None
            cls._instance.p_runner = None
        return cls._instance

    def start_components(self):
        """启动所有组件"""
        self.start_mitmproxy()
        self.start_task_runner()

    def start_mitmproxy(self):
        """启动 mitmproxy"""
        if self.p_mitm and self.p_mitm.poll() is None:
            logger.info("mitmproxy 已在运行中")
            return

        logger.info(f"正在启动 mitmproxy 拦截器 (端口: {settings.MITM_PROXY_PORT})...")
        addon_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../interceptor/addons.py"))
        
        cmd = [
            "mitmdump",
            "-q",
            "-s", addon_path,
            "-p", str(settings.MITM_PROXY_PORT)
        ]
        
        try:
            # 在 Windows 下使用 creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
            # 以便能够正确杀掉子进程
            creationflags = 0
            if sys.platform == "win32":
                creationflags = subprocess.CREATE_NEW_PROCESS_GROUP
                
            self.p_mitm = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=creationflags
            )
            logger.success("mitmproxy 启动成功")
        except Exception as e:
            logger.error(f"mitmproxy 启动失败: {e}")

    def start_task_runner(self):
        """启动任务处理器 (以子进程方式运行 python 脚本)"""
        if self.p_runner and self.p_runner.poll() is None:
            logger.info("任务处理器已在运行中")
            return

        logger.info("正在启动任务处理器...")
        
        # 使用当前解释器运行 TaskRunner 的独立入口
        runner_script = os.path.abspath(os.path.join(os.path.dirname(__file__), "runner_entry.py"))
        
        # 如果入口文件不存在，先创建一个简单的
        if not os.path.exists(runner_script):
            self._create_runner_entry(runner_script)

        cmd = [sys.executable, runner_script]
        
        try:
            creationflags = 0
            if sys.platform == "win32":
                creationflags = subprocess.CREATE_NEW_PROCESS_GROUP

            self.p_runner = subprocess.Popen(
                cmd,
                creationflags=creationflags
            )
            logger.success("任务处理器启动成功")
        except Exception as e:
            logger.error(f"任务处理器启动失败: {e}")

    def _create_runner_entry(self, path):
        """创建任务处理器的独立启动入口"""
        content = """
import sys
import os
import asyncio
from loguru import logger

# 确保项目根目录在 path 中
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from src.core.engine.runner import TaskRunner
from src.utils.logger_config import setup_logging

async def main():
    setup_logging()
    logger.info("TaskRunner 子进程已启动")
    try:
        runner = TaskRunner()
        await runner.run()
    except Exception as e:
        logger.error(f"TaskRunner 运行异常: {e}")

if __name__ == "__main__":
    asyncio.run(main())
"""
        with open(path, "w", encoding="utf-8") as f:
            f.write(content.strip())

    def stop_all(self):
        """停止所有组件"""
        if self.p_mitm:
            logger.info("正在停止 mitmproxy...")
            self.p_mitm.terminate()
            self.p_mitm = None
            
        if self.p_runner:
            logger.info("正在停止任务处理器...")
            self.p_runner.terminate()
            self.p_runner = None
        
        logger.info("所有组件已停止")

    def get_status(self):
        """获取组件状态"""
        return {
            "mitmproxy": "running" if self.p_mitm and self.p_mitm.poll() is None else "stopped",
            "runner": "running" if self.p_runner and self.p_runner.poll() is None else "stopped"
        }

scanner_manager = ScannerManager()
