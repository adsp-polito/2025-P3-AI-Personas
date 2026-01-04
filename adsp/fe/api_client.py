"""API client for backend communication."""

import base64
import requests
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass


@dataclass
class APIClient:
    """Client for interacting with the backend API."""
    
    base_url: str
    username: Optional[str] = None
    token: Optional[str] = None
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with authentication."""
        headers = {"Content-Type": "application/json"}
        if self.username and self.token:
            headers["X-User"] = self.username
            headers["X-Token"] = self.token
        return headers
    
    def health_check(self) -> bool:
        """Check if the API server is healthy."""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except Exception:
            return False
    
    def register_user(self, username: str, token: str) -> bool:
        """Register a new user with the authentication service."""
        try:
            response = requests.post(
                f"{self.base_url}/v1/auth/register",
                json={"user": username, "token": token},
                timeout=5,
            )
            return response.status_code == 200
        except Exception:
            return False
    
    def validate_auth(self, username: str, token: str) -> bool:
        """Validate user credentials."""
        try:
            response = requests.post(
                f"{self.base_url}/v1/auth/validate",
                json={"user": username, "token": token},
                timeout=5,
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("authorized", False)
            return False
        except Exception:
            return False
    
    def list_personas(self) -> List[Dict[str, Any]]:
        """Get list of available personas."""
        try:
            response = requests.get(
                f"{self.base_url}/v1/personas",
                headers=self._get_headers(),
                timeout=10,
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("personas", [])
            return []
        except Exception:
            return []
    
    def get_persona_profile(self, persona_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed profile for a specific persona."""
        try:
            response = requests.get(
                f"{self.base_url}/v1/personas/{persona_id}/profile",
                headers=self._get_headers(),
                timeout=10,
            )
            if response.status_code == 200:
                return response.json()
            return None
        except Exception:
            return None
    
    def get_system_prompt(self, persona_id: str) -> Optional[str]:
        """Get system prompt for a persona."""
        try:
            response = requests.get(
                f"{self.base_url}/v1/personas/{persona_id}/system-prompt",
                headers=self._get_headers(),
                timeout=10,
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("system_prompt")
            return None
        except Exception:
            return None
    
    def send_chat_message(
        self,
        persona_id: str,
        query: str,
        session_id: Optional[str] = None,
        top_k: int = 5,
        persona_display_name: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Send a chat message and get response."""
        try:
            payload = {
                "persona_id": persona_id,
                "query": query,
                "top_k": top_k,
            }
            if session_id:
                payload["session_id"] = session_id
            if persona_display_name:
                payload["persona_display_name"] = persona_display_name
            
            response = requests.post(
                f"{self.base_url}/v1/chat",
                json=payload,
                headers=self._get_headers(),
                timeout=30,
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("response")
            return None
        except Exception as e:
            print(f"Error sending chat message: {e}")
            return None
    
    def upload_file(
        self,
        filename: str,
        content: Union[bytes, str, Path],
        bucket: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Upload a file to the ingestion service.
        
        Args:
            filename: Name of the file
            content: File content as bytes, string path, or Path object
            bucket: Optional bucket name (uses default if not specified)
        
        Returns:
            Upload response with bucket, key, and size_bytes, or None on error
        """
        try:
            # Handle different content types
            if isinstance(content, (str, Path)):
                with open(content, "rb") as f:
                    file_bytes = f.read()
            else:
                file_bytes = content
            
            # Encode to base64
            content_base64 = base64.b64encode(file_bytes).decode("utf-8")
            
            payload = {
                "filename": filename,
                "content_base64": content_base64,
            }
            if bucket:
                payload["bucket"] = bucket
            
            response = requests.post(
                f"{self.base_url}/v1/ingestion/upload",
                json=payload,
                headers=self._get_headers(),
                timeout=60,
            )
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"Error uploading file: {e}")
            return None
    
    def generate_report(
        self,
        persona_id: str,
        insights: List[str],
    ) -> Optional[Dict[str, Any]]:
        """Generate a report for a persona.
        
        Args:
            persona_id: ID of the persona
            insights: List of insights to include in the report
        
        Returns:
            Report response with path to generated report, or None on error
        """
        try:
            payload = {"insights": insights}
            
            response = requests.post(
                f"{self.base_url}/v1/reports/{persona_id}",
                json=payload,
                headers=self._get_headers(),
                timeout=60,
            )
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"Error generating report: {e}")
            return None