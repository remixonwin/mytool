#!/usr/bin/env python3
import asyncio
import json
import os
import subprocess
import sys
from datetime import datetime
from typing import Any, Dict


def ensure_venv():
    """Ensure we're running in the virtual environment with all dependencies."""
    venv_dir = os.path.join(os.getcwd(), ".venv")
    if not os.path.exists(venv_dir):
        print("Creating virtual environment...")
        subprocess.run(["python3", "-m", "venv", ".venv"], check=True)

    # Activate virtual environment
    venv_python = os.path.join(venv_dir, "bin", "python")
    if sys.executable != venv_python:
        # Re-run this script with the venv Python
        os.execl(venv_python, venv_python, *sys.argv)

    try:
        import importlib.util

        # Check for required packages
        required_packages = ["fast_agent_mcp", "openai"]
        for package in required_packages:
            if importlib.util.find_spec(package) is None:
                raise ImportError(f"Package {package} not found")

    except ImportError:
        print("Installing dependencies...")
        subprocess.run([venv_python, "-m", "pip", "install", "-e", "."], check=True)


def main():
    """Main entry point for the pre-commit hook."""
    try:
        ensure_venv()

        # Now that we're in the venv with dependencies, import our modules
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        sys.path.insert(0, project_root)

        from src.mcp.server import ProjectTrackerServer

        class ProjectTracker:
            def __init__(self):
                self.server = ProjectTrackerServer()
                self.setup_deepseek()
                self.data_dir = os.path.join(os.getcwd(), ".project-data")
                os.makedirs(self.data_dir, exist_ok=True)

            def setup_deepseek(self):
                """Configure DeepSeek API client."""
                api_key = os.getenv("DEEPSEEK_API_KEY")
                if not api_key:
                    print("Warning: DEEPSEEK_API_KEY not set")
                    return

                # Import here to ensure it's available
                import openai

                openai.api_key = api_key
                openai.api_base = "https://api.deepseek.com/v1"

            async def analyze_changes(self) -> Dict[str, Any]:
                """Analyze git changes using DeepSeek API."""
                try:
                    # Get staged files
                    result = subprocess.run(
                        ["git", "diff", "--cached", "--name-only"],
                        capture_output=True,
                        text=True,
                    )
                    staged_files = result.stdout.strip().split("\n")

                    if not staged_files or staged_files == [""]:
                        return {"status": "no_changes"}

                    # Get diff content
                    diff_result = subprocess.run(
                        ["git", "diff", "--cached"],
                        capture_output=True,
                        text=True,
                    )
                    diff_content = diff_result.stdout

                    # Skip analysis if DEEPSEEK_API_KEY is not set
                    if not os.getenv("DEEPSEEK_API_KEY"):
                        return {
                            "status": "success",
                            "files_changed": staged_files,
                            "analysis": "Analysis skipped - DEEPSEEK_API_KEY not set",
                            "timestamp": datetime.utcnow().isoformat(),
                        }

                    # Import here to ensure it's available after setup
                    import openai

                    response = await openai.ChatCompletion.acreate(
                        model="deepseek-chat",
                        messages=[
                            {
                                "role": "system",
                                "content": (
                                    "You are a project management assistant. Analyze the "
                                    "following git diff and provide insights about the changes."
                                ),
                            },
                            {
                                "role": "user",
                                "content": f"Git diff to analyze:\n{diff_content}",
                            },
                        ],
                    )

                    analysis = response.choices[0].message.content
                    return {
                        "status": "success",
                        "files_changed": staged_files,
                        "analysis": analysis,
                        "timestamp": datetime.utcnow().isoformat(),
                    }

                except Exception as e:
                    print(f"Error analyzing changes: {str(e)}")
                    return {"status": "error", "error": str(e)}

            def save_analysis(self, analysis: Dict[str, Any]):
                """Save analysis results to the data store."""
                timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                filepath = os.path.join(self.data_dir, f"analysis_{timestamp}.json")

                with open(filepath, "w") as f:
                    json.dump(analysis, f, indent=2)

            async def run(self) -> int:
                """Run the pre-commit hook."""
                try:
                    # Analyze changes
                    analysis = await self.analyze_changes()
                    if analysis["status"] == "error":
                        print("Failed to analyze changes")
                        return 1
                    elif analysis["status"] == "no_changes":
                        print("No changes to analyze")
                        return 0

                    # Save analysis results
                    self.save_analysis(analysis)

                    # Update project status via MCP server
                    await self.server.handle_get_project_status({"detailed": True})

                    print("Project analysis completed successfully")
                    return 0

                except Exception as e:
                    print(f"Error in pre-commit hook: {str(e)}")
                    return 1

        tracker = ProjectTracker()
        exit_code = asyncio.run(tracker.run())
        sys.exit(exit_code)

    except Exception as e:
        print(f"Error in pre-commit hook setup: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
