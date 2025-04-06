from notion.api import NotionAPI
from notion.config import NotionConfig
import time

def create_example_database(notion: NotionAPI, root_page_id: str) -> str:
    """創建示例數據庫"""
    initial_properties = {
        "Name": {"title": {}},
        "Description": {"rich_text": {}},
        "Priority": {
            "select": {
                "options": [
                    {"name": "High", "color": "red"},
                    {"name": "Medium", "color": "yellow"},
                    {"name": "Low", "color": "green"}
                ]
            }
        },
        "Tags": {
            "multi_select": {
                "options": [
                    {"name": "Work", "color": "blue"},
                    {"name": "Personal", "color": "green"},
                    {"name": "Urgent", "color": "red"}
                ]
            }
        },
        "Due Date": {"date": {}},
        "Complete": {"checkbox": {}},
        "Score": {"number": {}},
        "Website": {"url": {}},
        "Contact": {"email": {}},
        "Phone": {"phone_number": {}},
        "File": {"files": {}}  # 添加 Files & Media 屬性
    }

    example_db = notion.create_database(
        parent_page_id=root_page_id,
        title="Example Database",
        properties=initial_properties
    )

    if not example_db:
        print("創建數據庫失敗")
        return None

    database_id = example_db["id"]
    print(f"創建的數據庫 ID: {database_id}")
    return database_id

def add_relation_property(notion: NotionAPI, database_id: str):
    """添加關聯屬性到數據庫"""
    # 首先只添加關聯屬性
    relation_property = {
        "Related Tasks": {
            "relation": {
                "database_id": database_id,
                "single_property": {}
            }
        }
    }
    
    # 更新數據庫添加關聯屬性
    response = notion.update_database(database_id, properties=relation_property)
    
    # 確保關聯屬性創建成功
    if response:
        print("關聯屬性創建成功")
        # 等待一下確保關聯屬性已經生效
        time.sleep(1)
        
        # 然後添加 Rollup 屬性
        rollup_properties = {
            "Total Score": {
                "rollup": {
                    "relation_property_name": "Related Tasks",
                    "rollup_property_name": "Score",  # 必須指定
                    "function": "sum"  # 使用字符串而不是枚舉
                }
            },
            "Task Count": {
                "rollup": {
                    "relation_property_name": "Related Tasks",
                    "rollup_property_name": "Name",  # 對於計數，使用任何存在的屬性都可以
                    "function": "count"
                }
            }
        }
        
        # 更新數據庫添加 Rollup 屬性
        response = notion.update_database(database_id, properties=rollup_properties)
        if response:
            print("Rollup 屬性創建成功")
            return True
    
    return False

def create_page_relation(notion: NotionAPI, database_id: str, page_ids: list):
    """創建頁面之間的關聯"""
    if len(page_ids) >= 2:
        relation_update = {
            "Name": {
                "title": [{"text": {"content": "Task 2 (Updated)"}}]
            },
            "Related Tasks": {
                "relation": [{"id": page_ids[0]}]
            }
        }
        
        # 在創建關聯之前先確認屬性存在
        properties = notion.get_database_properties(database_id)
        if "Related Tasks" not in properties:
            print("關聯屬性尚未創建成功，請稍後再試")
            return False
            
        result = notion.create_page(database_id=database_id, properties=relation_update)
        if result:
            print("關聯頁面創建成功")
            return True
    
    return False

def create_example_pages(notion: NotionAPI, database_id: str) -> list:
    """創建示例頁面"""
    example_pages = [
        {
            "Name": {"title": [{"text": {"content": "High Priority Task"}}]},
            "Priority": {"select": {"name": "High"}},
            "Tags": {"multi_select": [{"name": "Work"}, {"name": "Urgent"}]},
            "Score": {"number": 90},
            "Complete": {"checkbox": False}
        },
        {
            "Name": {"title": [{"text": {"content": "Medium Priority Task"}}]},
            "Priority": {"select": {"name": "Medium"}},
            "Tags": {"multi_select": [{"name": "Personal"}]},
            "Score": {"number": 75},
            "Complete": {"checkbox": True}
        }
    ]

    created_pages = []
    for page_properties in example_pages:
        result = notion.create_page(
            database_id=database_id,
            properties=page_properties
        )
        if result:
            created_pages.append(result["id"])
            print(f"創建頁面成功: {page_properties['Name']['title'][0]['text']['content']}")
    
    # 等待一下確保頁面創建完成
    if created_pages:
        time.sleep(1)
    
    return created_pages

def add_files_property(notion: NotionAPI, database_id: str, property_name: str = "File"):
    """添加 Files & Media 屬性到數據庫
    
    Args:
        notion: NotionAPI 實例
        database_id: 數據庫 ID
        property_name: 屬性名稱，默認為 "File"
        
    Returns:
        bool: 是否成功添加屬性
    """
    # 定義 Files & Media 屬性
    files_property = {
        property_name: {
            "files": {}
        }
    }
    
    # 更新數據庫添加文件屬性
    response = notion.update_database(database_id, properties=files_property)
    
    if response:
        print(f"Files & Media 屬性 '{property_name}' 創建成功")
        return True
    
    return False

def update_page_with_file(notion: NotionAPI, database_id: str, property_name: str = "File", file_path: str = "image/1.png"):
    """更新頁面添加文件
    
    Args:
        notion: NotionAPI 實例
        database_id: 數據庫 ID
        property_name: 屬性名稱，默認為 "File"
        file_path: 文件路徑，默認為 "image/1.png"
        
    Returns:
        bool: 是否成功更新頁面
    """
    properties = {
        "Name": {
            "title": [{"text": {"content": "Page with File"}}]
        },
        property_name: {
            "files": [
                {
                    "name": file_path,
                    "type": "external",
                    "external": {
                        "url": file_path
                    }
                }
            ]
        }
    }
    
    result = notion.create_page(database_id=database_id, properties=properties)
    if result:
        print(f"成功創建頁面並添加文件: {file_path}")
        return True
    
    return False

def create_example_with_file(notion: NotionAPI, database_id: str):
    """創建帶有文件的示例"""
    # 1. 添加 Files & Media 屬性
    if add_files_property(notion, database_id):
        # 2. 創建頁面並添加文件
        update_page_with_file(notion, database_id)

# 移除所有模組層級的代碼執行
if __name__ == "__main__":
    # 這裡可以放測試代碼
    pass

