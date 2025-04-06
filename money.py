from notion.api import NotionAPI
import json
import time
import os
import csv
from datetime import datetime
from secrets import NOTION_TOKEN

# 目錄常量
BASE_DATA_DIR = 'data'
BASE_IMAGE_DIR = os.path.join(BASE_DATA_DIR, 'image')
EVENT_DIR = os.path.join(BASE_IMAGE_DIR, 'event')
MONTH_DIR = os.path.join(BASE_IMAGE_DIR, 'month')

# 配置信息
config = {
    'token': NOTION_TOKEN,
    "account": 'c952a61ecb4d41f190d2a038fd9cdf8f',
    "event": '85771a19b13941d9a3d9a8507c5d5345',
    "month": '0462f8e33dbe4635a266165e40e3527b',
}
# ============= 工具函數 =============
def time_it(func):
    """計時裝飾器"""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"{func.__name__} 執行時間: {end_time - start_time:.2f} 秒")
        return result
    return wrapper

def sanitize_filename(filename: str) -> str:
    """清理文件名，移除或替換不合法字符"""
    invalid_chars = '<>:"/\\|?*,'
    filename = filename.replace(', ', '_')
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    filename = filename.strip('. _')
    return filename if filename else 'untitled'

def get_file_timestamp(file_path: str) -> tuple:
    """獲取文件的創建和修改時間戳"""
    try:
        creation_time = os.stat(file_path).st_birthtime
    except AttributeError:
        creation_time = os.path.getmtime(file_path)
    mod_time = os.path.getmtime(file_path)
    return creation_time, mod_time

def format_timestamp(timestamp: float) -> str:
    """將時間戳格式化為字符串"""
    return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

def parse_timestamp(timestamp_str: str) -> float:
    """將時間字符串解析為時間戳"""
    try:
        return datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S').timestamp()
    except (ValueError, TypeError):
        return 0

def ensure_directory(directory: str):
    """確保目錄存在"""
    os.makedirs(directory, exist_ok=True)

def safe_file_operation(func):
    """文件操作的安全裝飾器"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(f"文件操作失敗: {str(e)}")
            return None
    return wrapper

@safe_file_operation
def read_json_file(file_path: str) -> dict:
    """安全地讀取 JSON 文件"""
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

@safe_file_operation
def write_json_file(file_path: str, data: dict):
    """安全地寫入 JSON 文件"""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

@safe_file_operation
def read_csv_file(file_path: str) -> list:
    """安全地讀取 CSV 文件"""
    if not os.path.exists(file_path):
        return []
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        return list(reader)

@safe_file_operation
def write_csv_file(file_path: str, data: list):
    """安全地寫入 CSV 文件"""
    with open(file_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(data)

def log_success(message: str):
    """記錄成功信息"""
    print(f"✓ {message}")

def log_error(message: str):
    """記錄錯誤信息"""
    print(f"✗ {message}")

def log_info(message: str):
    """記錄一般信息"""
    print(f"! {message}")

# ============= 文件操作相關函數 =============
def get_file_creation_time(file_path: str) -> str:
    """獲取文件的創建時間"""
    creation_time, _ = get_file_timestamp(file_path)
    return format_timestamp(creation_time)

def get_file_modification_time(file_path: str) -> str:
    """獲取文件的最後修改時間"""
    _, mod_time = get_file_timestamp(file_path)
    return format_timestamp(mod_time)

def init_data_directory():
    """初始化數據目錄結構和記錄文件"""
    for directory in [BASE_DATA_DIR, BASE_IMAGE_DIR, EVENT_DIR, MONTH_DIR]:
        ensure_directory(directory)
    
    csv_path = os.path.join(BASE_IMAGE_DIR, 'image_records.csv')
    if not os.path.exists(csv_path):
        create_image_record(csv_path)
        log_success(f"已創建圖片記錄文件: {csv_path}")
    else:
        log_info(f"圖片記錄文件已存在: {csv_path}")

# ============= Notion API 相關函數 =============
@time_it
def get_database_properties(notion: NotionAPI, database_id: str):
    """獲取數據庫屬性"""
    return notion.get_database_properties(database_id)

@time_it
def get_event_pages(notion: NotionAPI, database_id: str, specific_props: list = None, limit: int = None):
    """獲取數據庫中的頁面屬性"""
    query_start = time.time()
    page_size = min(100, limit) if limit else 100  # Notion API 限制每次最多 100 條
    
    results = []
    has_more = True
    next_cursor = None
    total_fetched = 0
    
    while has_more and (limit is None or total_fetched < limit):
        print(f"正在獲取第 {total_fetched + 1} - {min(total_fetched + page_size, limit if limit else float('inf'))} 條記錄...")
        
        response = notion.query_database(
            database_id=database_id,
            page_size=page_size,
            start_cursor=next_cursor
        )
        
        if not response:
            break
            
        batch_results = response.get('results', [])
        remaining = limit - total_fetched if limit else None
        
        if remaining is not None and remaining < len(batch_results):
            batch_results = batch_results[:remaining]
            
        results.extend(batch_results)
        total_fetched += len(batch_results)
        
        has_more = response.get('has_more', False)
        next_cursor = response.get('next_cursor')
        
        print(f"已獲取 {total_fetched} 條記錄")
        print(f"是否還有更多: {has_more}")
        print(f"下一頁游標: {next_cursor}")
        
        if limit and total_fetched >= limit:
            print(f"已達到限制數量 {limit}，停止獲取")
            break
    
    query_end = time.time()
    print(f"\n查詢統計:")
    print(f"總獲取記錄數: {total_fetched}")
    print(f"查詢耗時: {query_end - query_start:.2f} 秒")
    
    if not results:
        return []
        
    pages_data = []
    total_props_time = 0
    
    for page in results:
        page_id = page['id']
        prop_start = time.time()
        props = notion.get_formatted_page_properties(
            page_id,
            specific_props,
            raw_page_data=page
        )
        prop_end = time.time()
        
        prop_time = prop_end - prop_start
        total_props_time += prop_time
        
        props['page_id'] = page_id
        pages_data.append(props)
        
    print(f"屬性處理總時間: {total_props_time:.2f} 秒")
    print(f"平均每條記錄處理時間: {total_props_time/len(pages_data):.2f} 秒")
    
    return pages_data

def get_select_colors(notion: NotionAPI, database_id: str):
    """獲取數據庫中所有 select 類型屬性的所有可能選項及其顏色"""
    # 獲取數據庫屬性
    properties = notion.get_database_properties(database_id)
    
    # 打印調試信息
    print("\n數據庫屬性：")
    print(json.dumps(properties, indent=2, ensure_ascii=False))
    
    select_colors = {}
    
    # 遍歷所有屬性
    for prop_name, prop_data in properties.items():
        if isinstance(prop_data, dict):
            prop_type = prop_data.get('type')
            
            if prop_type == 'select':
                # 處理單選屬性
                options = prop_data.get('select', {}).get('options', [])
                if options:
                    select_colors[prop_name] = {
                        option['name']: {
                            'color': option['color'],
                            'id': option['id']
                        }
                        for option in options
                    }
            
            elif prop_type == 'multi_select':
                # 處理多選屬性
                options = prop_data.get('multi_select', {}).get('options', [])
                if options:
                    select_colors[prop_name] = {
                        option['name']: {
                            'color': option['color'],
                            'id': option['id']
                        }
                        for option in options
                    }
    
    # 打印調試信息
    print("\n選項顏色信息：")
    for prop_name, colors in select_colors.items():
        print(f"\n{prop_name}:")
        for name, data in colors.items():
            print(f"  - {name}: {data['color']}")
    
    return select_colors

def save_select_options(notion: NotionAPI, database_id: str, load_from_file: bool = False):
    """獲取並保存數據庫中的 select 選項信息"""
    # 確保目錄存在
    os.makedirs(BASE_DATA_DIR, exist_ok=True)
    json_path = os.path.join(BASE_DATA_DIR, 'select_color.json')
    
    if load_from_file:
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    print("\n=== 獲取 Select 選項信息 ===")
    select_options = notion.get_database_select_options(database_id)
    
    # 打印調試信息
    print("\n選項信息：")
    for prop_name, data in select_options.items():
        print(f"\n{prop_name} ({data['type']}):")
        for option in data['options']:
            print(f"  - {option['name']}: {option['color']}")
    
    # 保存到文件
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(select_options, f, ensure_ascii=False, indent=2)
    
    print(f"\n選項信息已保存到 {json_path}")
    return select_options

def get_relation_table(notion: NotionAPI, load_from_file: bool = True):
    """獲取並保存關聯表"""
    # 確保目錄存在
    os.makedirs(BASE_DATA_DIR, exist_ok=True)
    json_path = os.path.join(BASE_DATA_DIR, 'relation_table.json')
    
    if load_from_file:
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    relation_table = {}
    
    # 獲取事件數據庫的頁面
    event_pages = get_event_pages(
        notion,
        database_id=config['event'],
        specific_props=['Title', 'Date']
    )
    
    # 獲取月份數據庫的頁面
    month_pages = get_event_pages(
        notion,
        database_id=config['month'],
        specific_props=['月份']
    )
    
    # 處理事件頁面
    for page in event_pages:
        if 'Title' in page and 'Date' in page:
            relation_table[page['page_id']] = f"{page['Title']}【{page['Date']}】"
    
    # 處理月份頁面
    for page in month_pages:
        if '月份' in page:
            relation_table[page['page_id']] = page['月份']

    # 保存到文件
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(relation_table, f, ensure_ascii=False, indent=2)
    
    print(f"已保存 {len(relation_table)} 條記錄到 {json_path}")
    return relation_table

# ============= 圖片記錄相關函數 =============
def create_image_record(csv_path: str) -> None:
    """創建新的圖片記錄文件"""
    headers = ['圖片名稱', '圖片創建時間', 'Imgur上傳時間', 'Imgur連結']
    write_csv_file(csv_path, [headers])
    log_success(f"創建新的圖片記錄文件: {csv_path}")

def get_image_record(image_path: str) -> tuple:
    """從 CSV 中獲取圖片記錄"""
    csv_path = os.path.join(BASE_IMAGE_DIR, 'image_records.csv')
    image_name = os.path.basename(image_path)
    
    if not os.path.exists(csv_path):
        create_image_record(csv_path)
        return None, None, None
    
    records = read_csv_file(csv_path)
    if not records or len(records) < 2:  # 至少需要標題行和一行數據
        return None, None, None
    
    for row in records[1:]:  # 跳過標題行
        if row[0] == image_name:
            return row[1], row[2], row[3]
    
    return None, None, None

def update_image_record(image_path: str, img_url: str = None):
    """更新或創建圖片記錄"""
    csv_path = os.path.join(BASE_IMAGE_DIR, 'image_records.csv')
    temp_path = os.path.join(BASE_IMAGE_DIR, 'temp_records.csv')
    
    image_name = os.path.basename(image_path)
    creation_time = get_file_creation_time(image_path)
    current_time = format_timestamp(time.time())
    
    if not os.path.exists(csv_path):
        create_image_record(csv_path)
        if img_url:
            write_csv_file(csv_path, [
                ['圖片名稱', '圖片創建時間', 'Imgur上傳時間', 'Imgur連結'],
                [image_name, creation_time, current_time, img_url]
            ])
            log_success(f"添加新記錄: {image_name}")
        return
    
    records = read_csv_file(csv_path)
    if not records:
        return
    
    headers = records[0]
    found = False
    updated_records = [headers]
    
    for row in records[1:]:
        if row[0] == image_name:
            if img_url:
                updated_records.append([image_name, creation_time, current_time, img_url])
                log_success(f"更新記錄: {image_name}")
            else:
                updated_records.append(row)
            found = True
        else:
            updated_records.append(row)
    
    if not found and img_url:
        updated_records.append([image_name, creation_time, current_time, img_url])
        log_success(f"添加新記錄: {image_name}")
    
    write_csv_file(temp_path, updated_records)
    os.replace(temp_path, csv_path)

def collect_png_files() -> dict:
    """收集所有 PNG 文件，以文件名為鍵"""
    png_files = {}
    for directory in [EVENT_DIR, MONTH_DIR]:
        files = os.listdir(directory)
        files.sort()
        for file in files:
            if file.endswith('.png'):
                file_name = file
                full_path = os.path.join(directory, file)
                if file_name not in png_files:
                    png_files[file_name] = full_path
                else:
                    if directory == EVENT_DIR:
                        png_files[file_name] = full_path
    return png_files

def read_image_records(csv_path: str) -> dict:
    """讀取現有的圖片記錄"""
    records = {}
    if os.path.exists(csv_path):
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader)
            for row in reader:
                if len(row) >= 5:
                    file_name = row[0]
                    records[file_name] = {
                        'file_name': file_name,
                        'full_path': row[1],
                        'modification_time': row[2],
                        'url': row[3],
                        'upload_notion_time': row[4]
                    }
    return records

def save_records(records: dict, csv_path: str):
    """保存所有記錄到 CSV"""
    with open(csv_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['file_name', 'file_path', 'modification_time', 'url', 'upload_notion_time'])
        for record in records.values():
            writer.writerow([
                record['file_name'],
                record['full_path'], 
                record['modification_time'], 
                record['url'],
                record['upload_notion_time']
            ])

def process_file(file_name: str, file_path: str, records: dict, notion: NotionAPI, bypass_imgur: bool):
    """處理單個文件的更新檢查和上傳"""
    current_time = datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%Y-%m-%d %H:%M:%S')
    record = records.get(file_name)

    need_upload = False
    need_save = False
    
    if not record:
        # 新文件，創建記錄
        print(f"{file_name} - 當前修改時間: {current_time}, 記錄中的時間: 無記錄")
        records[file_name] = {
            'file_name': file_name,
            'full_path': file_path,
            'modification_time': current_time,
            'url': '',
            'upload_notion_time': ''
        }
        need_upload = True
        need_save = True
    else:
        if not record['url']:
            # 存在記錄但沒有 URL
            print(f"{file_name} - URL 不存在")
            need_upload = True
        if record['modification_time'] != current_time:
            # 文件已修改，更新時間
            print(f"{file_name} - 當前修改時間: {current_time}, 記錄中的時間: {record['modification_time']}")
            records[file_name].update({
                'modification_time': current_time,
                'full_path': file_path  # 確保路徑也更新
            })
            need_upload = True
            need_save = True

    if need_upload and not bypass_imgur:
        try:
            imgur_url = notion.upload_to_imgur(file_path)
            if imgur_url:
                records[file_name].update({
                    'url': imgur_url,
                    'modification_time': current_time,
                    'full_path': file_path
                })
                print(f"✓ {file_name}: {imgur_url}")
                need_save = True  # 確保有新的 URL 時一定會保存
            else:
                print(f"✗ 上傳 {file_name} 到 Imgur 失敗")
        except Exception as e:
            print(f"✗ 上傳 {file_name} 到 Imgur 失敗: {str(e)}")
    
    if need_save:
        save_records(records, os.path.join(BASE_IMAGE_DIR, 'image_records.csv'))

def scan_image_records(notion: NotionAPI, bypass_imgur: bool = False):
    """掃描圖片記錄並上傳到 Imgur"""
    print("\n掃描並更新圖片記錄...")
    
    try:
        # 確保目錄存在
        os.makedirs(EVENT_DIR, exist_ok=True)
        os.makedirs(MONTH_DIR, exist_ok=True)
        
        # 設置 CSV 文件路徑
        csv_path = os.path.join(BASE_IMAGE_DIR, 'image_records.csv')
        
        # 讀取現有記錄
        records = read_image_records(csv_path)
        
        # 收集並處理所有 PNG 文件
        png_files = collect_png_files()
        for file_name, file_path in png_files.items():
            process_file(file_name, file_path, records, notion, bypass_imgur)
        
        return True
        
    except Exception as e:
        print(f"✗ 掃描圖片記錄時發生錯誤: {str(e)}")
        return False

# ============= Notion 圖片上傳相關類和函數 =============
class NotionImageUploader:
    """處理 Notion 圖片上傳的類"""
    
    def __init__(self, notion_api, max_retries=5, retry_delay=30):
        self.notion = notion_api
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        # 確保目錄和 CSV 文件存在
        os.makedirs(BASE_IMAGE_DIR, exist_ok=True)
        csv_path = os.path.join(BASE_IMAGE_DIR, 'image_records.csv')
        if not os.path.exists(csv_path):
            create_image_record(csv_path)
        
    def upload_with_retry(self, file_path: str) -> str:
        """嘗試上傳圖片到 Imgur，帶重試機制
        
        Args:
            file_path: 圖片文件路徑
            
        Returns:
            str: Imgur 圖片 URL
            
        Raises:
            Exception: 上傳失敗時拋出異常
        """
        retries_left = self.max_retries
        
        while retries_left > 0:
            try:
                print(f"嘗試上傳 {file_path}（剩餘重試次數：{retries_left}）")
                return self.notion.upload_to_imgur(file_path)
            except Exception as e:
                retries_left -= 1
                if "Too Many Requests" in str(e) and retries_left > 0:
                    print(f"遇到請求限制，等待 {self.retry_delay} 秒後重試...")
                    time.sleep(self.retry_delay)
                else:
                    raise Exception(f"上傳失敗：{str(e)}")
    
    def get_graph_paths(self, event_name: str) -> dict:
        """獲取事件相關的圖表文件路徑，並確保目錄存在
        
        Args:
            event_name: 事件名稱
                
        Returns:
            dict: 包含三種圖表路徑的字典
        """
        base_filename = sanitize_filename(event_name)
        
        # 確保基礎目錄和子目錄都存在
        os.makedirs(EVENT_DIR, exist_ok=True)
        os.makedirs(MONTH_DIR, exist_ok=True)
        
        # 根據文件名判斷應該使用哪個目錄
        save_dir = MONTH_DIR if '月' in event_name else EVENT_DIR
        
        # 構建圖表路徑
        paths = {}
        for chart_type in ['總圓餅圖', '廷圓餅圖', '雰圓餅圖']:
            file_name = f"{base_filename}.png" if chart_type == '總圓餅圖' else f"{base_filename} ({chart_type[0]}).png"
            paths[chart_type] = os.path.join(save_dir, file_name)
            
            # 檢查文件是否存在
            if not os.path.exists(paths[chart_type]):
                print(f"警告: 找不到圖表文件 {paths[chart_type]}")
        
        return paths
    
    def get_file_hash(self, file_path: str) -> str:
        """獲取文件的 MD5 哈希值，用於檢查文件是否變更
        
        Args:
            file_path: 文件路徑
            
        Returns:
            str: 文件的 MD5 哈希值
        """
        import hashlib
        with open(file_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    
    def get_current_image_url(self, page_id: str, property_name: str) -> str:
        """獲取 Notion 頁面中當前的圖片 URL
        
        Args:
            page_id: Notion 頁面 ID
            property_name: 屬性名稱
            
        Returns:
            str: 當前的圖片 URL，如果沒有則返回空字符串
        """
        try:
            properties = self.notion.get_page_properties(page_id)
            files = properties.get(property_name, {}).get('files', [])
            if files and files[0].get('type') == 'external':
                return files[0]['external']['url']
        except Exception:
            pass
        return ''
    
    def check_updates_needed(self, page_id: str, graph_paths: dict) -> dict:
        """檢查哪些圖表需要更新
        
        Args:
            page_id: Notion 頁面 ID
            graph_paths: 圖表路徑字典
            
        Returns:
            dict: 需要更新的圖表路徑字典
        """
        updates_needed = {}
        
        for prop_name, file_path in graph_paths.items():
            if os.path.exists(file_path):
                current_url = self.get_current_image_url(page_id, prop_name)
                if not current_url:
                    updates_needed[prop_name] = file_path
                    print(f"{prop_name} 需要上傳：當前無圖片")
        
        return updates_needed
    
    def upload_and_update(self, page_id: str, event_title: str) -> bool:
        """上傳圖表並更新 Notion 頁面"""
        try:
            # 獲取圖表路徑
            graph_paths = self.get_graph_paths(event_title)
            
            # 檢查哪些圖表需要更新
            updates_needed = self.check_updates_needed(page_id, graph_paths)
            
            if not updates_needed:
                return True
            
            # 只有當有需要更新的圖表時才顯示事件標題
            print(f"\n更新事件：{event_title}")
            
            # 上傳需要更新的圖表
            success = True
            for prop_name, file_path in updates_needed.items():
                try:
                    if self.notion.update_page_file(page_id, file_path, prop_name):
                        print(f"✓ {prop_name}")
                    else:
                        print(f"✗ {prop_name}")
                        success = False
                    
                    # 添加延遲，避免連續請求
                    time.sleep(5)
                    
                except Exception as e:
                    print(f"✗ {prop_name}")
                    success = False
                    continue
            
            return success
            
        except Exception as e:
            print(f"✗ 錯誤: {str(e)}")
            return False

def upload_single_event_graphs(notion: NotionAPI, page_id: str, relation_table: dict):
    """上傳單個事件的圖表到 Notion"""
    # 獲取事件標題
    event_title = relation_table.get(page_id)
    if not event_title:
        print(f"在 relation_table 中找不到頁面 ID: {page_id}")
        return
    
    # 創建上傳器實例並執行上傳
    uploader = NotionImageUploader(notion)
    success = uploader.upload_and_update(page_id, event_title)
    
    if success:
        print(f"完成事件 {event_title} 的圖表上傳")
    else:
        print(f"事件 {event_title} 的圖表上傳失敗")

def read_image_records_for_update() -> dict:
    """讀取圖片記錄"""
    records = {}
    csv_path = os.path.join(BASE_IMAGE_DIR, 'image_records.csv')
    if os.path.exists(csv_path):
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader)  # 跳過標題行
            for row in reader:
                if len(row) >= 5:
                    file_name = row[0]  # file_name
                    # 嘗試將時間字符串轉換為時間戳
                    try:
                        mod_time = datetime.strptime(row[2], '%Y-%m-%d %H:%M:%S').timestamp() if row[2] else 0  # modification_time
                    except (ValueError, TypeError):
                        mod_time = 0
                        
                    try:
                        upload_time = datetime.strptime(row[4], '%Y-%m-%d %H:%M:%S').timestamp() if row[4] else 0  # upload_notion_time
                    except (ValueError, TypeError):
                        upload_time = 0
                        
                    records[file_name] = {
                        'url': row[3],  # url
                        'modification_time': mod_time,
                        'upload_notion_time': upload_time,
                        'file_path': row[1],  # full_path
                        'original_row': row  # 保存原始行數據
                    }
    return records

def save_single_record(file_name: str, record: dict):
    """保存單個圖片記錄到 CSV 文件"""
    csv_path = os.path.join(BASE_IMAGE_DIR, 'image_records.csv')
    temp_path = os.path.join(BASE_IMAGE_DIR, 'temp_records.csv')
    
    try:
        # 讀取原始文件以獲取所有記錄
        all_records = {}
        if os.path.exists(csv_path):
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                headers = next(reader)  # 跳過標題行
                for row in reader:
                    if len(row) >= 5:
                        all_records[row[0]] = row
        
        # 更新需要更新的記錄
        if file_name in all_records:
            row = all_records[file_name]
            # 更新上傳時間
            row[4] = datetime.fromtimestamp(record['upload_notion_time']).strftime('%Y-%m-%d %H:%M:%S')
            all_records[file_name] = row
        
        # 寫入所有記錄到臨時文件
        with open(temp_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['file_name', 'full_path', 'modification_time', 'url', 'upload_notion_time'])
            for row in all_records.values():
                writer.writerow(row)
        
        # 替換原文件
        os.replace(temp_path, csv_path)
        print(f"✓ 已更新 {file_name} 的記錄")
        
    except Exception as e:
        print(f"保存圖片記錄時發生錯誤: {str(e)}")
        if os.path.exists(temp_path):
            os.remove(temp_path)

def update_single_chart(notion: NotionAPI, page_id: str, prop_name: str, 
                       file_name: str, record: dict) -> bool:
    """更新單個圖表"""
    try:
        # 檢查時間戳
        mod_time = record.get('modification_time', 0)
        upload_time = record.get('upload_notion_time', 0)
        
        # 如果上傳時間晚於修改時間，跳過更新
        if upload_time and upload_time > mod_time:
            print(f"跳過 {prop_name}: 上傳時間晚於修改時間")
            return True
            
        # 更新 Notion 頁面的圖片
        if notion.update_page_file(page_id, None, prop_name, record['url']):
            print(f"✓ {prop_name}: {file_name}")
            # 更新上傳時間
            record['upload_notion_time'] = time.time()
            # 立即保存更新後的記錄
            save_single_record(file_name, record)
            return True
        else:
            print(f"✗ 更新 {prop_name} 失敗: {file_name}")
            return False
    except Exception as e:
        print(f"✗ 更新 {prop_name} 時發生錯誤: {str(e)}")
        return False

def update_notion_pie_charts(notion: NotionAPI, relation_table: dict):
    """根據 relation_table 更新 Notion 頁面的圓餅圖"""
    try:
        # 讀取圖片記錄
        image_records = read_image_records_for_update()
        
        for page_id, event_title in relation_table.items():
            # 定義三種圖表的文件名和屬性名
            charts = {
                '總圓餅圖': f"{event_title}.png",
                '廷圓餅圖': f"{event_title} (廷).png",
                '雰圓餅圖': f"{event_title} (雰).png"
            }
            
            # 檢查是否所有圖表都需要跳過
            all_skipped = True
            for prop_name, file_name in charts.items():
                record = image_records.get(file_name)
                if record and record['url']:
                    mod_time = record.get('modification_time', 0)
                    upload_time = record.get('upload_notion_time', 0)
                    if not (upload_time and upload_time > mod_time):
                        all_skipped = False
                        break
            
            if all_skipped:
                # print(f"處理: {event_title} pass")
                continue
            
            print(f"\n處理事件: {event_title}")
            
            # 更新每個圓餅圖
            for prop_name, file_name in charts.items():
                record = image_records.get(file_name)
                if record and record['url']:
                    update_single_chart(notion, page_id, prop_name, file_name, record)
                else:
                    print(f"! {prop_name} 找不到圖片記錄或 URL: {file_name}")
            
            # 添加延遲避免請求過快
            time.sleep(1)
        
        return True
        
    except Exception as e:
        print(f"✗ 更新圓餅圖時發生錯誤: {str(e)}")
        return False

# ============= 數據處理相關函數 =============
def read_old_data(full_data_path: str) -> list:
    """讀取舊數據"""
    old_data = []
    if os.path.exists(full_data_path):
        with open(full_data_path, 'r', encoding='utf-8') as f:
            old_data = json.load(f)
    return old_data

def get_old_page_ids(old_data: list) -> set:
    """獲取舊數據的 page_id 集合"""
    return {record.get('page_id') for record in old_data}

def process_page_properties(notion: NotionAPI, page: dict, specific_props: list, relation_table: dict) -> dict:
    """處理單個頁面的屬性"""
    page_id = page['id']
    props = notion.get_formatted_page_properties(
        page_id,
        specific_props,
        raw_page_data=page
    )
    props['page_id'] = page_id
    
    # 處理關聯數據
    for key, value in props.items():
        if isinstance(value, str):
            if value in relation_table:
                props[key] = {'id': value, 'title': relation_table[value]}
        elif isinstance(value, dict) and 'number' in value:
            props[key] = value['number']
    
    return props

def collect_affected_events(new_records: list) -> set:
    """收集受影響的事件"""
    affected_events = set()
    
    for record in new_records:
        # 檢查重大事件支出列表
        if record.get('💥 重大事件支出列表'):
            event_data = record.get('💥 重大事件支出列表')
            if isinstance(event_data, dict) and 'title' in event_data:
                event_title = event_data['title']
                affected_events.add(event_title)
        
        # 檢查單月支出列表
        if record.get('💵 單月支出列表'):
            month_data = record.get('💵 單月支出列表')
            if isinstance(month_data, dict) and 'title' in month_data:
                month_title = month_data['title']
                affected_events.add(month_title)
    
    return affected_events

def collect_affected_data(all_data: list, affected_events: set) -> list:
    """收集受影響事件的完整數據"""
    affected_data = set()
    
    for record in all_data:
        # 檢查重大事件支出列表
        if record.get('💥 重大事件支出列表'):
            event_data = record.get('💥 重大事件支出列表')
            if isinstance(event_data, dict) and 'title' in event_data:
                event_title = event_data['title']
                if event_title in affected_events:
                    affected_data.add(json.dumps(record, ensure_ascii=False, sort_keys=True))
        
        # 檢查單月支出列表
        if record.get('💵 單月支出列表'):
            month_data = record.get('💵 單月支出列表')
            if isinstance(month_data, dict) and 'title' in month_data:
                month_title = month_data['title']
                if month_title in affected_events:
                    affected_data.add(json.dumps(record, ensure_ascii=False, sort_keys=True))
    
    return [json.loads(record) for record in affected_data]

def save_data_to_files(full_data_path: str, affected_data_path: str, 
                      new_records: list, old_data: list, affected_data: list):
    """保存數據到文件"""
    # 更新 full_account_data.json
    if new_records:
        updated_data = old_data + new_records
        with open(full_data_path, 'w', encoding='utf-8') as f:
            json.dump(updated_data, f, ensure_ascii=False, indent=2)
        print(f"已更新 {full_data_path}")
    
    # 保存受影響的數據
    if affected_data:
        with open(affected_data_path, 'w', encoding='utf-8') as f:
            json.dump(affected_data, f, ensure_ascii=False, indent=2)
        print(f"已保存受影響的數據到 {affected_data_path}")

def get_data_from_notion(notion, relation_table, specific_props, limit=None):
    """從 Notion 獲取數據並處理"""
    start_time = time.time()
    print("開始獲取數據...")
    
    # 確保目錄存在
    os.makedirs(BASE_DATA_DIR, exist_ok=True)
    full_data_path = os.path.join(BASE_DATA_DIR, 'full_account_data.json')
    affected_data_path = os.path.join(BASE_DATA_DIR, 'affected_charts_data.json')
    
    # 讀取舊數據
    old_data = read_old_data(full_data_path)
    old_page_ids = get_old_page_ids(old_data)
    
    # 獲取新數據
    pages_data = []
    new_records = []
    has_more = True
    next_cursor = None
    total_fetched = 0
    page_size = min(100, limit) if limit else 100
    
    while has_more and (limit is None or total_fetched < limit):
        print(f"正在獲取第 {total_fetched + 1} - {min(total_fetched + page_size, limit if limit else float('inf'))} 條記錄...")
        
        response = notion.query_database(
            database_id=config['account'],
            page_size=page_size,
            start_cursor=next_cursor
        )
        
        if not response:
            break
            
        batch_results = response.get('results', [])
        remaining = limit - total_fetched if limit else None
        
        if remaining is not None and remaining < len(batch_results):
            batch_results = batch_results[:remaining]
        
        # 處理每條記錄
        for page in batch_results:
            page_id = page['id']
            
            # 如果遇到重複的 page_id，立即停止獲取
            if page_id in old_page_ids:
                print(f"遇到重複記錄，停止獲取")
                has_more = False
                break
            
            # 處理頁面屬性
            props = process_page_properties(notion, page, specific_props, relation_table)
            pages_data.append(props)
            new_records.append(props)
            total_fetched += 1
        
        # 如果已經遇到重複記錄，跳出外層循環
        if not has_more:
            break
            
        has_more = response.get('has_more', False)
        next_cursor = response.get('next_cursor')
        
        print(f"已獲取 {total_fetched} 條記錄")
        print(f"是否還有更多: {has_more}")
        print(f"下一頁游標: {next_cursor}")
        
        if limit and total_fetched >= limit:
            print(f"已達到限制數量 {limit}，停止獲取")
            break
    
    # 處理受影響的圖表數據
    affected_events = set()
    if new_records:
        affected_events = collect_affected_events(new_records)
        print(f"受影響的事件: {', '.join(affected_events)}")
        
        # 從所有數據中收集受影響事件的完整數據
        all_data = old_data + new_records
        affected_data = collect_affected_data(all_data, affected_events)
        
        # 保存數據到文件
        save_data_to_files(full_data_path, affected_data_path, new_records, old_data, affected_data)
        print(f"受影響的事件: {', '.join(affected_events)}")
    
    end_time = time.time()
    total_time = end_time - start_time
    
    print(f"\n執行完成！")
    print(f"總執行時間: {total_time:.2f} 秒")
    print(f"新增記錄數: {len(new_records)}")
    
    return new_records, affected_events

# ============= 主要流程函數 =============
def init_notion_api():
    """初始化 Notion API 和基本配置"""
    notion = NotionAPI(config['token'])
    load_from_file = True
    update_mode = 'affected'
    return notion, load_from_file, update_mode

def setup_notion_data(notion: NotionAPI, load_from_file: bool):
    """設置 Notion 數據和屬性"""
    save_select_options(notion, config['account'], load_from_file=load_from_file)
    relation_table = get_relation_table(notion, load_from_file=load_from_file)
    specific_props = ['品項','支出NTD', '類別', '日期', '廷 | 雰', '屬性', '💥 重大事件支出列表', '💵 單月支出列表', '折扣/抵']
    return relation_table, specific_props

def process_charts(affected_events: set, update_mode: str):
    """處理圖表生成"""
    from draw_graph import ChartManager
    chart_manager = ChartManager()
    
    if update_mode == 'affected':
        log_info("使用受影響的數據源更新圖表...")
        chart_manager.draw_graph(affected_events, source='affected')
    else:
        log_info("使用完整數據源更新圖表...")
        chart_manager.draw_graph(source='full')

def update_notion_page(notion: NotionAPI, relation_table: dict) -> bool:
    """更新 Notion 頁面的圓餅圖"""
    if update_notion_pie_charts(notion, relation_table):
        log_success("Notion 頁面更新成功")
        return True
    else:
        log_error("Notion 頁面更新失敗")
        return False

def process_new_records(notion: NotionAPI, relation_table: dict, specific_props: list, update_mode: str):
    """處理新記錄並更新圖表"""
    # 獲取新數據並處理受影響的圖表
    new_records, affected_events = get_data_from_notion(notion, relation_table, specific_props, limit=None)
    
    if new_records:
        # 生成圖表
        process_charts(affected_events, update_mode)

        # 掃描並更新圖片記錄
        bypass_imgur = False
        scan_image_records(notion, bypass_imgur=bypass_imgur)

        # 更新 Notion 頁面的圓餅圖
        update_notion_page(notion, relation_table)
    else:
        log_info("沒有新記錄，無需更新圖表")

def redraw_charts(titles: list):
    """重繪指定標題的圖表"""
    from draw_graph import ChartManager
    chart_manager = ChartManager()
    
    log_info("使用完整數據源重繪圖表...")
    chart_manager.draw_graph(target_events=set(titles), source='full')

def redraw_single_title(titles: list):
    """重繪指定標題的圖表"""
    log_info(f"開始重繪標題：{', '.join(titles)}")
    
    # 初始化 Notion API
    notion = NotionAPI(config['token'])
    
    # 獲取關聯表
    relation_table = get_relation_table(notion, load_from_file=True)
    
    # 生成圖表
    redraw_charts(titles)
    
    # 掃描並更新圖片記錄
    bypass_imgur = False
    scan_image_records(notion, bypass_imgur=bypass_imgur)
    
    # 更新 Notion 頁面的圓餅圖
    update_notion_page(notion, relation_table)
    log_success(f"完成重繪標題：{', '.join(titles)}")

def process_normal_update():
    """處理正常的更新流程"""
    # 初始化 Notion API 和配置
    notion, load_from_file, update_mode = init_notion_api()
    
    # 設置 Notion 數據和屬性
    relation_table, specific_props = setup_notion_data(notion, load_from_file)
    
    # 處理新記錄並更新圖表
    process_new_records(notion, relation_table, specific_props, update_mode)

def main():
    """主函數"""
    # 初始化數據目錄
    init_data_directory()
    
    # 設置要重繪的標題（如果有的話）
    titles_to_redraw = None  # ["2025, 01月", "2025, 02月", "2025, 03月", "2025, 04月"]  # 如果要重繪，取消註釋並設置標題列表
    
    if titles_to_redraw:
        # 如果指定了要重繪的標題，只執行重繪
        redraw_single_title(titles_to_redraw)
    else:
        # 否則執行正常的更新流程
        process_normal_update()

if __name__ == "__main__":
    main()
