"""
Async Label Studio client for concurrent API operations
"""
import logging
from typing import List, Dict, Any, Optional
import httpx
from config import settings

logger = logging.getLogger(__name__)


class AsyncLabelStudioClient:
    """Async client for Label Studio API operations"""
    
    def __init__(self, host: str = None, api_key: str = None):
        self.host = host or settings.label_studio_host
        self.api_key = api_key or settings.label_studio_api_key
        self.headers = {
            "Authorization": f"Token {self.api_key}",
            "Content-Type": "application/json"
        }
        self.client = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.client = httpx.AsyncClient(
            base_url=self.host,
            headers=self.headers,
            timeout=30.0
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.client:
            await self.client.aclose()
    
    async def get_projects(self) -> List[Dict[str, Any]]:
        """Get all projects"""
        response = await self.client.get("/api/projects")
        response.raise_for_status()
        data = response.json()
        
        # Handle paginated response
        if isinstance(data, dict) and 'results' in data:
            return data['results']
        return data if isinstance(data, list) else []
    
    async def get_project(self, project_id: int) -> Dict[str, Any]:
        """Get project by ID"""
        response = await self.client.get(f"/api/projects/{project_id}")
        response.raise_for_status()
        return response.json()
    
    async def export_annotations(
        self, 
        project_id: int, 
        export_format: str = "JSON"
    ) -> List[Dict[str, Any]]:
        """Export annotations in specified format"""
        response = await self.client.get(
            f"/api/projects/{project_id}/export",
            params={"exportType": export_format}
        )
        response.raise_for_status()
        return response.json()
    
    async def get_tasks(self, project_id: int) -> List[Dict[str, Any]]:
        """Get all tasks for a project"""
        response = await self.client.get(f"/api/projects/{project_id}/tasks")
        response.raise_for_status()
        data = response.json()
        
        # Handle paginated response
        if isinstance(data, dict) and 'results' in data:
            return data['results']
        return data if isinstance(data, list) else []
    
    async def create_webhook(
        self, 
        project_id: int, 
        url: str, 
        events: List[str] = None
    ) -> Dict[str, Any]:
        """Create a webhook for project events"""
        if events is None:
            events = [
                "ANNOTATION_CREATED",
                "ANNOTATION_UPDATED",
                "ANNOTATION_DELETED"
            ]
        
        webhook_data = {
            "url": url,
            "send_payload": True,
            "send_for_all_actions": False,
            "headers": {},
            "is_active": True
        }
        
        response = await self.client.post(
            f"/api/webhooks?project={project_id}",
            json=webhook_data
        )
        response.raise_for_status()
        return response.json()


# Singleton instance for reuse
_async_client_instance = None


async def get_async_ls_client() -> AsyncLabelStudioClient:
    """Get or create async Label Studio client"""
    global _async_client_instance
    if _async_client_instance is None:
        _async_client_instance = AsyncLabelStudioClient()
    return _async_client_instance
