import os
import json
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path

class ProjectDataStore:
    """Handles persistent storage of project tracking data."""

    def __init__(self, base_dir: Optional[str] = None):
        """Initialize the data store with an optional base directory."""
        if base_dir is None:
            base_dir = os.path.join(os.getcwd(), '.project-data')
        self.base_dir = Path(base_dir)
        self.ensure_directories()

    def ensure_directories(self):
        """Create necessary directories if they don't exist."""
        for subdir in ['tasks', 'progress', 'metrics', 'analyses']:
            (self.base_dir / subdir).mkdir(parents=True, exist_ok=True)

    def _get_filepath(self, category: str, name: str) -> Path:
        """Get the full filepath for a data file."""
        return self.base_dir / category / f"{name}.json"

    def save_data(self, category: str, name: str, data: Dict[str, Any]):
        """Save data to a JSON file in the specified category."""
        filepath = self._get_filepath(category, name)
        data['last_updated'] = datetime.utcnow().isoformat()
        
        with filepath.open('w') as f:
            json.dump(data, f, indent=2)

    def load_data(self, category: str, name: str) -> Optional[Dict[str, Any]]:
        """Load data from a JSON file in the specified category."""
        filepath = self._get_filepath(category, name)
        
        if not filepath.exists():
            return None
        
        with filepath.open('r') as f:
            return json.load(f)

    def list_files(self, category: str) -> list[str]:
        """List all data files in a category."""
        category_dir = self.base_dir / category
        if not category_dir.exists():
            return []
        
        return [f.stem for f in category_dir.glob('*.json')]

    def save_task(self, task_id: str, task_data: Dict[str, Any]):
        """Save task data."""
        self.save_data('tasks', task_id, task_data)

    def load_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Load task data."""
        return self.load_data('tasks', task_id)

    def save_progress(self, progress_id: str, progress_data: Dict[str, Any]):
        """Save progress data."""
        self.save_data('progress', progress_id, progress_data)

    def load_progress(self, progress_id: str) -> Optional[Dict[str, Any]]:
        """Load progress data."""
        return self.load_data('progress', progress_id)

    def save_metrics(self, metrics_id: str, metrics_data: Dict[str, Any]):
        """Save metrics data."""
        self.save_data('metrics', metrics_id, metrics_data)

    def load_metrics(self, metrics_id: str) -> Optional[Dict[str, Any]]:
        """Load metrics data."""
        return self.load_data('metrics', metrics_id)

    def save_analysis(self, analysis_data: Dict[str, Any]):
        """Save an analysis result with a timestamp-based ID."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        self.save_data('analyses', f'analysis_{timestamp}', analysis_data)

    def get_latest_analysis(self) -> Optional[Dict[str, Any]]:
        """Get the most recent analysis result."""
        analyses = sorted(self.list_files('analyses'), reverse=True)
        if not analyses:
            return None
        return self.load_data('analyses', analyses[0])

    def get_project_status(self) -> Dict[str, Any]:
        """Get the current project status including tasks, progress, and metrics."""
        return {
            'tasks': {
                'count': len(self.list_files('tasks')),
                'items': [self.load_task(task_id) for task_id in self.list_files('tasks')]
            },
            'progress': {
                'latest': self.load_progress('latest'),
                'history': [self.load_progress(pid) for pid in self.list_files('progress')]
            },
            'metrics': {
                'latest': self.load_metrics('latest'),
                'history': [self.load_metrics(mid) for mid in self.list_files('metrics')]
            },
            'last_analysis': self.get_latest_analysis()
        }