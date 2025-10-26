"""
Label Studio client for managing projects and annotations
"""
import requests
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging

from core.config import settings

logger = logging.getLogger(__name__)


class LabelStudioClient:
    """Client for interacting with Label Studio API"""
    
    def __init__(self, host: str = None, api_key: str = None):
        self.host = host or settings.label_studio_host
        self.api_key = api_key or settings.label_studio_api_key
        self.headers = {
            "Authorization": f"Token {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make HTTP request to Label Studio API"""
        url = f"{self.host}/api/{endpoint}"
        response = requests.request(method, url, headers=self.headers, **kwargs)
        response.raise_for_status()
        return response
    
    def get_projects(self) -> List[Dict[str, Any]]:
        """Get all projects"""
        response = self._make_request("GET", "projects/")
        data = response.json()
        # Label Studio returns paginated results
        if isinstance(data, dict) and 'results' in data:
            return data['results']
        return data
    
    def get_project(self, project_id: int) -> Dict[str, Any]:
        """Get project by ID"""
        response = self._make_request("GET", f"projects/{project_id}/")
        return response.json()
    
    def create_project(self, title: str, description: str = "", label_config: str = None) -> Dict[str, Any]:
        """Create a new project"""
        data = {
            "title": title,
            "description": description
        }
        if label_config:
            data["label_config"] = label_config
        
        response = self._make_request("POST", "projects/", json=data)
        return response.json()
    
    def get_tasks(self, project_id: int) -> List[Dict[str, Any]]:
        """Get all tasks for a project"""
        response = self._make_request("GET", f"projects/{project_id}/tasks/")
        return response.json()
    
    def get_annotations(self, project_id: int) -> List[Dict[str, Any]]:
        """Get all annotations for a project"""
        response = self._make_request("GET", f"projects/{project_id}/export", params={"exportType": "JSON"})
        return response.json()
    
    def setup_webhook(self, project_id: int, webhook_url: str, send_payload: bool = True) -> Dict[str, Any]:
        """Setup webhook for a project"""
        data = {
            "url": webhook_url,
            "send_payload": send_payload,
            "is_active": True
        }
        response = self._make_request("POST", f"webhooks?project={project_id}", json=data)
        return response.json()
    
    def get_webhooks(self, project_id: int) -> List[Dict[str, Any]]:
        """Get all webhooks for a project"""
        response = self._make_request("GET", f"webhooks?project={project_id}")
        return response.json()
    
    def create_image_annotation_project(self, project_name: str) -> Dict[str, Any]:
        """Create a project configured for image annotation"""
        label_config = """
        <View>
          <Image name="image" value="$image"/>
          <RectangleLabels name="label" toName="image">
            <Label value="Object1" background="green"/>
            <Label value="Object2" background="blue"/>
            <Label value="Object3" background="red"/>
          </RectangleLabels>
        </View>
        """
        
        project = self.create_project(
            title=project_name,
            description="Image annotation project for ClearML pipeline",
            label_config=label_config
        )
        
        logger.info(f"Created Label Studio project: {project['title']} (ID: {project['id']})")
        return project
    
    def import_tasks(self, project_id: int, image_urls: List[str]) -> Dict[str, Any]:
        """Import image tasks from URLs"""
        tasks = [{"data": {"image": url}} for url in image_urls]
        response = self._make_request("POST", f"projects/{project_id}/import", json=tasks)
        return response.json()
    
    def export_annotations(self, project_id: int, export_format: str = "JSON") -> List[Dict[str, Any]]:
        """Export annotations in specified format"""
        response = self._make_request(
            "GET", 
            f"projects/{project_id}/export",
            params={"exportType": export_format}
        )
        return response.json()
