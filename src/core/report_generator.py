import os
import datetime
from typing import List, Dict

class ReportGenerator:
    """
    报告生成器：将漏洞发现汇总为 Markdown 报告
    """
    def __init__(self, output_dir: str = "reports"):
        self.output_dir = output_dir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

    def generate(self, findings: List[Dict], request_id: str, project_name: str = "Default") -> str:
        """
        生成 Markdown 报告
        """
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        filename = f"report_{project_name}_{request_id}.md"
        filepath = os.path.join(self.output_dir, filename)

        md_content = f"""# 漏洞扫描报告 (Vulnerability Scan Report)

**生成时间**: {timestamp}
**项目名称**: {project_name}
**任务 ID**: {request_id}

---

## 1. 扫描概览 (Summary)

共发现 **{len(findings)}** 个潜在漏洞。

| 漏洞类型 | 目标 URL | 参数 | 风险等级 |
| :--- | :--- | :--- | :--- |
"""
        for f in findings:
            # 缩短 URL 显示，避免表格撑破
            display_url = f['url'] if len(f['url']) < 50 else f['url'][:47] + "..."
            md_content += f"| {f['type']} | {display_url} | `{f.get('parameter', 'N/A')}` | **High** |\n"

        md_content += "\n--- \n\n## 2. 漏洞详情 (Detailed Findings)\n\n"

        for i, f in enumerate(findings, 1):
            md_content += f"### {i}. {f['type']}\n\n"
            md_content += f"#### [ 基础信息 ]\n"
            md_content += f"- **目标 URL**: `{f['url']}`\n"
            md_content += f"- **注入参数**: `{f.get('parameter', 'N/A')}`\n"
            md_content += f"- **漏洞 Payload**: `{f.get('payload', 'N/A')}`\n"
            md_content += f"- **检测证据**: {f.get('evidence', 'N/A')}\n\n"

            # 添加原始请求包展示
            if f.get("original_request"):
                orig = f["original_request"]
                md_content += f"#### [ 原始请求包 ]\n"
                md_content += f"```http\n"
                md_content += f"{orig.get('method', 'GET')} {orig.get('url', f['url'])}\n"
                for k, v in orig.get("headers", {}).items():
                    md_content += f"{k}: {v}\n"
                if orig.get("body"):
                    md_content += f"\n{orig['body']}\n"
                md_content += f"```\n\n"

        md_content += """---
*报告由 WebAgent 自动生成*
"""
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(md_content)

        return filepath
