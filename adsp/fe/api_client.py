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

    def _safe_json(self, response: requests.Response) -> Dict[str, Any]:
        """Parse JSON payload safely and return a dictionary fallback."""
        try:
            data = response.json()
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}
    
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
                data = self._safe_json(response)
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
                data = self._safe_json(response)
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
                data = self._safe_json(response)
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
                timeout=(5, 120),  # (connect, read)
            )
            if response.status_code == 200:
                data = self._safe_json(response)
                return data.get("response")
            return None
        except Exception as e:
            print(f"Error sending chat message: {e}")
            return None

    def create_group(
        self,
        composition: List[Dict[str, Any]],
        group_name: Optional[str] = None,
        mode: str = "random",
        sampling_ratio: float = 0.7,
        include_names: bool = True,
        countries: Optional[List[str]] = None,
        seed: Optional[int] = None,
    ) -> Optional[Dict[str, Any]]:
        """Create a respondent group."""
        try:
            payload: Dict[str, Any] = {
                "composition": composition,
                "mode": mode,
                "sampling_ratio": sampling_ratio,
                "include_names": include_names,
            }
            if group_name is not None:
                payload["group_name"] = group_name
            if countries is not None:
                payload["countries"] = countries
            if seed is not None:
                payload["seed"] = seed

            response = requests.post(
                f"{self.base_url}/api/groups",
                json=payload,
                headers=self._get_headers(),
                timeout=60,
            )
            if response.status_code == 200:
                return self._safe_json(response)
            return None
        except Exception as e:
            print(f"Error creating respondent group: {e}")
            return None

    def list_groups(self, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """List respondent groups with pagination."""
        try:
            response = requests.get(
                f"{self.base_url}/api/groups",
                params={"page": page, "page_size": page_size},
                headers=self._get_headers(),
                timeout=30,
            )
            if response.status_code == 200:
                data = self._safe_json(response)
                if "items" in data and "paging" in data:
                    return data
            return {
                "items": [],
                "paging": {
                    "page": page,
                    "page_size": page_size,
                    "total_items": 0,
                    "total_pages": 1,
                },
            }
        except Exception as e:
            print(f"Error listing respondent groups: {e}")
            return {
                "items": [],
                "paging": {
                    "page": page,
                    "page_size": page_size,
                    "total_items": 0,
                    "total_pages": 1,
                },
            }

    def list_available_countries(self) -> List[Dict[str, Any]]:
        """List available countries supported for respondent generation."""
        try:
            response = requests.get(
                f"{self.base_url}/api/groups/countries",
                headers=self._get_headers(),
                timeout=30,
            )
            if response.status_code == 200:
                data = self._safe_json(response)
                countries = data.get("countries", [])
                return countries if isinstance(countries, list) else []
            return []
        except Exception as e:
            print(f"Error listing available countries: {e}")
            return []

    def get_group(self, group_id: str, include_full_profiles: bool = False) -> Optional[Dict[str, Any]]:
        """Get one respondent group by id."""
        try:
            response = requests.get(
                f"{self.base_url}/api/groups/{group_id}",
                params={"include_full_profiles": include_full_profiles},
                headers=self._get_headers(),
                timeout=60,
            )
            if response.status_code == 200:
                return self._safe_json(response)
            return None
        except Exception as e:
            print(f"Error fetching respondent group: {e}")
            return None

    def list_surveys(self, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """List surveys with pagination."""
        try:
            response = requests.get(
                f"{self.base_url}/api/surveys",
                params={"page": page, "page_size": page_size},
                headers=self._get_headers(),
                timeout=30,
            )
            if response.status_code == 200:
                data = self._safe_json(response)
                if "items" in data and "paging" in data:
                    return data
            return {
                "items": [],
                "paging": {
                    "page": page,
                    "page_size": page_size,
                    "total_items": 0,
                    "total_pages": 1,
                },
            }
        except Exception as e:
            print(f"Error listing surveys: {e}")
            return {
                "items": [],
                "paging": {
                    "page": page,
                    "page_size": page_size,
                    "total_items": 0,
                    "total_pages": 1,
                },
            }

    def create_survey(
        self,
        title: str,
        description: str,
        questions: List[Dict[str, Any]],
        survey_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Create and persist a survey."""
        try:
            payload: Dict[str, Any] = {
                "title": title,
                "description": description,
                "questions": questions,
            }
            if survey_id:
                payload["survey_id"] = survey_id

            response = requests.post(
                f"{self.base_url}/api/surveys",
                json=payload,
                headers=self._get_headers(),
                timeout=60,
            )
            if response.status_code == 200:
                return self._safe_json(response)
            return None
        except Exception as e:
            print(f"Error creating survey: {e}")
            return None

    def get_survey(self, survey_id: str) -> Optional[Dict[str, Any]]:
        """Get one survey by id."""
        try:
            response = requests.get(
                f"{self.base_url}/api/surveys/{survey_id}",
                headers=self._get_headers(),
                timeout=60,
            )
            if response.status_code == 200:
                return self._safe_json(response)
            return None
        except Exception as e:
            print(f"Error fetching survey: {e}")
            return None

    def run_survey_simulation(
        self,
        survey_id: str,
        group_id: str,
        background: bool = True,
    ) -> Optional[Dict[str, Any]]:
        """Run a survey simulation for a given survey and respondent group."""
        try:
            response = requests.post(
                f"{self.base_url}/api/surveys/{survey_id}/simulate",
                params={"background": background},
                json={"group_id": group_id},
                headers=self._get_headers(),
                timeout=(5, 300),
            )
            if response.status_code == 200:
                return self._safe_json(response)
            return None
        except Exception as e:
            print(f"Error running survey simulation: {e}")
            return None

    def download_simulation_responses(
        self,
        survey_id: str,
        simulation_id: Optional[str] = None,
        format: str = "csv",
    ) -> Optional[Dict[str, Any]]:
        """Download simulation responses as CSV or JSON file content."""
        try:
            params: Dict[str, Any] = {"format": format}
            if simulation_id:
                params["simulation_id"] = simulation_id

            response = requests.get(
                f"{self.base_url}/api/surveys/{survey_id}/responses",
                params=params,
                headers=self._get_headers(),
                timeout=(5, 300),
            )
            if response.status_code == 200:
                filename = f"{survey_id}-{simulation_id or 'latest'}-responses.{format}"
                content_disposition = response.headers.get("Content-Disposition", "")
                if "filename=" in content_disposition:
                    filename = content_disposition.split("filename=")[-1].strip().strip('"')
                return {
                    "filename": filename,
                    "content_type": response.headers.get("Content-Type", "application/octet-stream"),
                    "content": response.content,
                }
            return None
        except Exception as e:
            print(f"Error downloading simulation responses: {e}")
            return None

    def get_simulation_response_details(
        self,
        survey_id: str,
        simulation_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Fetch structured response details for a simulation."""
        try:
            params: Dict[str, Any] = {}
            if simulation_id:
                params["simulation_id"] = simulation_id

            response = requests.get(
                f"{self.base_url}/api/surveys/{survey_id}/response-details",
                params=params,
                headers=self._get_headers(),
                timeout=(5, 300),
            )
            if response.status_code == 200:
                return self._safe_json(response)
            return None
        except Exception as e:
            print(f"Error fetching simulation response details: {e}")
            return None

    def compute_simulation_statistics(
        self,
        survey_id: str,
        simulation_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Compute statistics for a survey simulation."""
        try:
            params: Dict[str, Any] = {}
            if simulation_id:
                params["simulation_id"] = simulation_id

            response = requests.get(
                f"{self.base_url}/api/surveys/{survey_id}/statistics",
                params=params,
                headers=self._get_headers(),
                timeout=(5, 300),
            )
            if response.status_code == 200:
                return self._safe_json(response)
            return None
        except Exception as e:
            print(f"Error computing simulation statistics: {e}")
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
