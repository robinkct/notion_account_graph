from notion.api import NotionAPI

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
    return created_pages

def create_page_relation(notion: NotionAPI, database_id: str, page_ids: list):
    """創建頁面之間的關聯"""
    if len(page_ids) >= 2:
        relation_update = {
            "Name": {"title": [{"text": {"content": "Task 2 (Updated)"}}]},
            "Related Tasks": {
                "relation": [{"id": page_ids[0]}]
            }
        }
        notion.create_page(database_id=database_id, properties=relation_update)
