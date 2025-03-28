from typing import Any, Dict

from fast_agent_mcp import MCPServer, Resource, ResourceProvider, Tool

from ..agent.data_store import ProjectDataStore
from ..agent.project_manager import ProjectManager


class ProjectTrackerServer(MCPServer):
    def __init__(self):
        super().__init__("project-tracker")
        self.project_manager = ProjectManager()
        self.setup_tools()
        self.setup_resources()

    def setup_tools(self):
        """Set up the MCP tools for project tracking."""
        self.add_tool(
            Tool(
                name="get_project_status",
                description="Get current project status",
                input_schema={
                    "type": "object",
                    "properties": {
                        "detailed": {
                            "type": "boolean",
                            "default": False,
                            "description": "Whether to return detailed status",
                        }
                    },
                },
                handler=self.handle_get_project_status,
            )
        )

        self.add_tool(
            Tool(
                name="analyze_risks",
                description="Analyze project risks and dependencies",
                input_schema={
                    "type": "object",
                    "properties": {
                        "include_suggestions": {
                            "type": "boolean",
                            "default": False,
                            "description": "Whether to include risk mitigation suggestions",
                        }
                    },
                },
                handler=self.handle_analyze_risks,
            )
        )

        self.add_tool(
            Tool(
                name="generate_report",
                description="Generate a project report",
                input_schema={
                    "type": "object",
                    "properties": {
                        "format": {
                            "type": "string",
                            "enum": ["markdown", "json"],
                            "default": "markdown",
                            "description": "Output format for the report",
                        }
                    },
                },
                handler=self.handle_generate_report,
            )
        )

    def setup_resources(self):
        """Set up the MCP resources for project data."""
        self.add_resource_provider(ProjectDataProvider(self.project_manager.data_store))

    async def handle_get_project_status(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle the get_project_status tool."""
        detailed = args.get("detailed", False)
        return await self.project_manager.get_project_status(detailed)

    async def handle_analyze_risks(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle the analyze_risks tool."""
        include_suggestions = args.get("include_suggestions", False)
        return await self.project_manager.analyze_risks(include_suggestions)

    async def handle_generate_report(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle the generate_report tool."""
        report_format = args.get("format", "markdown")
        return await self.project_manager.generate_report(report_format)


class ProjectDataProvider(ResourceProvider):
    def __init__(self, data_store: ProjectDataStore):
        super().__init__()
        self.data_store = data_store

    async def get_resource(self, uri: str) -> Resource:
        """Get a project resource by URI."""
        if uri == "project://tasks":
            return Resource(
                uri=uri,
                content_type="application/json",
                data={"tasks": self.data_store.list_files("tasks")},
            )
        elif uri == "project://progress":
            return Resource(
                uri=uri,
                content_type="application/json",
                data={"progress": self.data_store.load_data("progress", "latest")},
            )
        elif uri == "project://metrics":
            return Resource(
                uri=uri,
                content_type="application/json",
                data={"metrics": self.data_store.load_data("metrics", "latest")},
            )
        return None


if __name__ == "__main__":
    server = ProjectTrackerServer()
    server.run()
