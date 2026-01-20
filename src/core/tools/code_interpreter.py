import sys
import asyncio
import tempfile
import os
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from loguru import logger

class PythonCodeSchema(BaseModel):
    code: str = Field(
        ..., 
        description="要执行的 Python 代码。注意：\n1. 必须使用 print() 函数输出你想要查看的结果，否则输出为空。\n2. 代码在独立的沙箱进程中运行，无法访问当前内存变量。\n3. 支持标准库，禁止危险操作。"
    )

@tool(args_schema=PythonCodeSchema)
async def execute_python_code(code: str) -> str:
    """
    Python 代码执行器 (沙箱模式)。
    """
    logger.info(f"正在沙箱(子进程)中执行 Python 代码...")
    
    # 创建临时文件
    # Windows 下必须 delete=False，否则无法被子进程读取
    # 显式指定 encoding='utf-8' 防止中文乱码
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as tmp:
            tmp.write(code)
            tmp_path = tmp.name
    except Exception as e:
        return f"❌ 创建临时文件失败: {e}"
        
    try:
        # 使用 asyncio.create_subprocess_exec 异步执行
        # 设置超时时间，防止死循环 (例如 10秒)
        # 使用当前解释器 sys.executable 确保环境一致性
        proc = await asyncio.create_subprocess_exec(
            sys.executable, tmp_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        try:
            # 等待执行结果，带超时控制
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=10.0)
        except asyncio.TimeoutError:
            try:
                proc.kill()
            except:
                pass
            return "❌ 代码执行超时 (限制 10 秒)"
            
        output = stdout.decode('utf-8', errors='replace').strip()
        error = stderr.decode('utf-8', errors='replace').strip()
        
        if proc.returncode != 0:
            logger.warning(f"代码执行出错: {error}")
            return f"❌ 执行出错:\n{error}"
            
        if not output:
            return "✅ 代码执行成功，但没有输出 (请使用 print 函数打印结果)。"
            
        return output

    except Exception as e:
        logger.error(f"沙箱执行发生系统错误: {e}")
        return f"❌ 沙箱执行发生系统错误: {str(e)}"
        
    finally:
        # 清理临时文件
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception as e:
                logger.warning(f"清理临时文件失败: {e}")
