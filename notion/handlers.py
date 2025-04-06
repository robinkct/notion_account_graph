import requests
import json
from .config import NotionConfig

class NotionRequestHandler:
    def __init__(self, token: str):
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Notion-Version": NotionConfig.API_VERSION,
        }

    def _make_request(self, method: str, url: str, data: dict = None) -> dict:
        """統一的請求處理方法，增強錯誤處理"""
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=self.headers,
                json=data if data else None
            )
            
            # 詳細的錯誤信息輸出
            if not response.ok:
                error_detail = response.json() if response.content else "No error details"
                print(f"API Error: {response.status_code}")
                print(f"URL: {url}")
                print(f"Request Data: {data}")
                print(f"Error Details: {error_detail}")
                return None
                
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"Network Error: {str(e)}")
            return None
        except json.JSONDecodeError as e:
            print(f"JSON Parsing Error: {str(e)}")
            return None
        except Exception as e:
            print(f"Unexpected Error: {str(e)}")
            return None