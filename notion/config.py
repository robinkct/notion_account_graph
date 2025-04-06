try:
    from .secrets import NOTION_TOKEN, IMGUR_CLIENT_ID
except ImportError:
    NOTION_TOKEN = ""  # 或者拋出錯誤
    IMGUR_CLIENT_ID = ""

class NotionConfig:
    API_VERSION = "2022-06-28"
    BASE_URL = "https://api.notion.com/v1"
    NOTION_TOKEN = NOTION_TOKEN
    IMGUR_CLIENT_ID = IMGUR_CLIENT_ID

    # 定義 property 類型枚舉
    class PropertyType:
        TITLE = "title"
        RICH_TEXT = "rich_text"
        NUMBER = "number"
        SELECT = "select"
        MULTI_SELECT = "multi_select"
        DATE = "date"
        CHECKBOX = "checkbox"
        URL = "url"
        EMAIL = "email"
        PHONE = "phone_number"
        RELATION = "relation"
        ROLLUP = "rollup"

    # 定義 block 類型枚舉
    class BlockType:
        PARAGRAPH = "paragraph"
        IMAGE = "image"
        HEADING_1 = "heading_1"
        HEADING_2 = "heading_2"
        HEADING_3 = "heading_3"

    class RollupType:
        """Rollup 函數類型"""
        COUNT = "count"
        COUNT_VALUES = "count_values"
        EMPTY = "empty"
        NOT_EMPTY = "not_empty"
        UNIQUE = "unique"
        SHOW_ORIGINAL = "show_original"
        SUM = "sum"
        AVERAGE = "average"
        MEDIAN = "median"
        MIN = "min"
        MAX = "max"
        RANGE = "range"
        PERCENT_EMPTY = "percent_empty"
        PERCENT_NOT_EMPTY = "percent_not_empty"
        PERCENT_PER_GROUP = "percent_per_group"