import base64
import requests
from typing import Union
from pathlib import Path
from .config import NotionConfig

class ImgurUploader:
    """處理圖片上傳到 Imgur 的類"""
    API_URL = "https://api.imgur.com/3/image"
    
    def __init__(self, client_id: str):
        self.headers = {'Authorization': f'Client-ID {client_id}'}
    
    def upload(self, image_path: Union[str, Path]) -> str:
        """上傳圖片到 Imgur 並返回 URL"""
        try:
            # 讀取圖片文件
            with open(image_path, 'rb') as image_file:
                image_data = base64.b64encode(image_file.read())
            
            # 上傳到 Imgur
            response = requests.post(
                self.API_URL,
                headers=self.headers,
                data={'image': image_data}
            )
            
            if response.status_code == 200:
                return response.json()['data']['link']
            else:
                raise Exception(f"上傳失敗: {response.json()['data']['error']}")
                
        except Exception as e:
            raise Exception(f"圖片上傳失敗: {str(e)}")

class BlockBuilder:
    def __init__(self, imgur_client_id: str = None):
        """
        初始化 BlockBuilder
        
        Args:
            imgur_client_id: Imgur API 的 client ID，用於上傳本地圖片
        """
        self.imgur_uploader = ImgurUploader(imgur_client_id) if imgur_client_id else None

    @staticmethod
    def text_block(content: str) -> dict:
        return {
            "object": "block",
            "type": NotionConfig.BlockType.PARAGRAPH,
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": content}}]
            }
        }

    def image_block(self, image: Union[str, Path], caption: str = None) -> dict:
        """
        創建圖片區塊，支持 URL 或本地圖片路徑
        
        Args:
            image: 圖片 URL 或本地圖片路徑
            caption: 圖片說明文字（可選）
        
        Returns:
            dict: Notion 圖片區塊格式的字典
        
        Raises:
            Exception: 當使用本地圖片但未設置 imgur_client_id 時
            Exception: 當圖片上傳失敗時
        """
        # 判斷是 URL 還是本地路徑
        image_url = image
        if not image.startswith(('http://', 'https://')):
            if not self.imgur_uploader:
                raise Exception("要上傳本地圖片需要提供 Imgur client ID")
            
            # 上傳本地圖片到 Imgur
            image_url = self.imgur_uploader.upload(image)

        # 創建基本圖片區塊
        block = {
            "object": "block",
            "type": NotionConfig.BlockType.IMAGE,
            "image": {
                "type": "external",
                "external": {"url": image_url}
            }
        }

        # 添加說明文字（如果有）
        if caption:
            block["image"]["caption"] = [
                {
                    "type": "text",
                    "text": {"content": caption}
                }
            ]

        return block
