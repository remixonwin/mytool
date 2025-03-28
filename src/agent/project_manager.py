import os
from datetime import datetime
from typing import Any, Dict

import openai

from .data_store import ProjectDataStore
from .task_manager import TaskManager


class ProjectManager:
    """Manages project tracking and analysis using DeepSeek API."""

    def __init__(self):
        """Initialize the project manager with its components."""
        self.data_store = ProjectDataStore()
        self.task_manager = TaskManager(self.data_store)
        self.setup_deepseek()

    def setup_deepseek(self):
        """Configure DeepSeek API client."""
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            raise ValueError("DEEPSEEK_API_KEY environment variable not set")

        openai.api_key = api_key
        openai.api_base = "https://api.deepseek.com/v1"

    async def get_project_status(self, detailed: bool = False) -> Dict[str, Any]:
        """Get current project status including tasks, progress, and metrics."""
        basic_status = self.data_store.get_project_status()

        if not detailed:
            return basic_status

        # Add AI-generated insights for detailed status
        tasks_summary = await self.task_manager.generate_task_summary()
        latest_analysis = self.data_store.get_latest_analysis()

        return {
            **basic_status,
            "ai_insights": {
                "task_summary": tasks_summary,
                "latest_analysis": latest_analysis,
            },
        }

    async def analyze_risks(self, include_suggestions: bool = False) -> Dict[str, Any]:
        """Analyze project risks and optionally provide mitigation suggestions."""
        try:
            # Gather project data for analysis
            project_status = await self.get_project_status(detailed=True)
            tasks = self.task_manager.list_tasks()

            # Prepare context for DeepSeek analysis
            context = {
                "tasks": tasks,
                "status": project_status,
                "latest_analysis": self.data_store.get_latest_analysis(),
            }

            system_content = (
                "You are a project risk analysis expert. Analyze the project data "
                "and identify potential risks and their severity."
            )

            if include_suggestions:
                system_content += (
                    " Also provide specific mitigation suggestions for each identified risk."
                )

            messages = [
                {"role": "system", "content": system_content},
                {
                    "role": "user",
                    "content": f"Project data to analyze:\n{str(context)}",
                },
            ]

            response = await openai.ChatCompletion.acreate(
                model="deepseek-chat", messages=messages
            )

            analysis = response.choices[0].message.content
            result = {
                "timestamp": datetime.utcnow().isoformat(),
                "analysis": analysis,
                "data_snapshot": {
                    "task_count": len(tasks),
                    "status_summary": project_status.get("tasks", {}).get("count", 0),
                },
            }

            # Save the risk analysis
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            self.data_store.save_data("analyses", f"risk_analysis_{timestamp}", result)
            return result

        except Exception as err:
            raise RuntimeError("Failed to analyze project risks") from err

    async def generate_report(self, report_format: str = "markdown") -> Dict[str, Any]:
        """Generate a comprehensive project report."""
        try:
            # Gather all necessary data
            status = await self.get_project_status(detailed=True)
            risks = await self.analyze_risks(include_suggestions=True)
            tasks = self.task_manager.list_tasks()

            # Prepare context for report generation
            context = {
                "project_status": status,
                "risk_analysis": risks,
                "tasks": tasks,
                "format": report_format,
            }

            report_prompt = (
                f"Generate a comprehensive project report in {report_format} format. "
                "Include status overview, task progress, risks, and recommendations."
            )

            response = await openai.ChatCompletion.acreate(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": report_prompt},
                    {
                        "role": "user",
                        "content": f"Project data for report:\n{str(context)}",
                    },
                ],
            )

            report_content = response.choices[0].message.content
            report = {
                "format": report_format,
                "content": report_content,
                "generated_at": datetime.utcnow().isoformat(),
                "metadata": {
                    "task_count": len(tasks),
                    "risk_count": len(risks.get("analysis", "").split("\n")),
                },
            }

            # Save the report
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            self.data_store.save_data("reports", f"report_{timestamp}", report)
            return report

        except Exception as err:
            raise RuntimeError("Failed to generate project report") from err

    async def process_commit_analysis(self, analysis: Dict[str, Any]):
        """Process and store commit analysis results."""
        if analysis.get("status") == "success":
            # Store the analysis
            self.data_store.save_analysis(analysis)

            # Update project metrics
            metrics = {
                "last_commit": {
                    "timestamp": analysis["timestamp"],
                    "files_changed": len(analysis["files_changed"]),
                    "analysis": analysis["analysis"],
                },
                "generated_at": datetime.utcnow().isoformat(),
            }
            self.data_store.save_metrics("latest", metrics)

            # Create task for significant changes
            if len(analysis["files_changed"]) > 5:
                await self.task_manager.create_task(
                    title="Review Major Code Changes",
                    description=f"Significant changes detected in commit:\n{analysis['analysis']}",
                    priority="high",
                )
