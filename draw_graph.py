import os
import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict
import json
from typing import Dict, List, Tuple, Set, Any
from dataclasses import dataclass

# 禁止顯示 macOS 輸入法警告
os.environ['TK_SILENCE_DEPRECATION'] = '1'
# 添加以下兩行來抑制額外的警告
os.environ['PYTHON_ENABLE_TKINTER'] = '0'
os.environ['PYTHONUTF8'] = '1'

# 設置中文字體
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'SimSun', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

# 配置常量
@dataclass
class Config:
    SHOW_PLOT: bool = False
    SAVE_PLOT: bool = True
    DPI: int = 300
    FIGSIZE: Tuple[int, int] = (15, 10)
    SMALL_PORTION_THRESHOLD: float = 0.03

# 目錄常量
@dataclass
class Paths:
    BASE_DATA_DIR: str = 'data'
    BASE_IMAGE_DIR: str = os.path.join(BASE_DATA_DIR, 'image')
    EVENT_DIR: str = os.path.join(BASE_IMAGE_DIR, 'event')
    MONTH_DIR: str = os.path.join(BASE_IMAGE_DIR, 'month')
    SELECT_COLOR_PATH: str = os.path.join(BASE_DATA_DIR, 'select_color.json')
    AFFECTED_CHARTS_DATA_PATH: str = os.path.join(BASE_DATA_DIR, 'affected_charts_data.json')
    FULL_ACCOUNT_DATA_PATH: str = os.path.join(BASE_DATA_DIR, 'full_account_data.json')

# Notion 顏色映射
NOTION_TO_MPL_COLORS = {
    'default': '#37352F',
    'gray': '#787774',
    'brown': '#9F6B53',
    'orange': '#D9730D',
    'yellow': '#CB912F',
    'green': '#448361',
    'blue': '#337EA9',
    'purple': '#9065B0',
    'pink': '#C14C8A',
    'red': '#D44C47'
}

class ChartDataProcessor:
    """處理圖表數據的類"""
    
    def __init__(self, data: List[Dict], valid_attributes: Set[str], valid_categories: Set[str]):
        self.data = data
        self.valid_attributes = valid_attributes
        self.valid_categories = valid_categories
        
    def get_expense_amount(self, record: Dict) -> float:
        """從記錄中獲取支出金額"""
        expense = record.get('支出NTD')
        if isinstance(expense, dict):
            return expense.get('number', 0)
        return float(expense) if isinstance(expense, (int, float)) else 0
    
    def process_expenses_by_person(self, record: Dict) -> Tuple[Dict, Dict]:
        """處理單條記錄的支出數據，根據記錄的 '廷 | 雰' 欄位進行分類"""
        ting_expenses = {'attribute': defaultdict(float), 'category': defaultdict(float)}
        feng_expenses = {'attribute': defaultdict(float), 'category': defaultdict(float)}
        
        expense = self.get_expense_amount(record)
        if not expense:
            return ting_expenses, feng_expenses
        
        share_info = record.get('廷 | 雰')
        if isinstance(share_info, dict):
            share_info = share_info.get('title', '')
        
        if share_info == '廷':
            target_dict = ting_expenses
        elif share_info == '雰':
            target_dict = feng_expenses
        else:
            half_expense = expense / 2
            ting_expenses['attribute'] = defaultdict(lambda: half_expense)
            ting_expenses['category'] = defaultdict(lambda: half_expense)
            feng_expenses['attribute'] = defaultdict(lambda: half_expense)
            feng_expenses['category'] = defaultdict(lambda: half_expense)
            return ting_expenses, feng_expenses
        
        attribute = record.get('屬性')
        if attribute and attribute in self.valid_attributes:
            target_dict['attribute'][attribute] = expense
        
        category = record.get('類別')
        if category and category in self.valid_categories:
            target_dict['category'][category] = expense
        
        return ting_expenses, feng_expenses

class ChartGenerator:
    """生成圖表的類"""
    
    def __init__(self, config: Config, paths: Paths):
        self.config = config
        self.paths = paths
        self._ensure_directories()
    
    def _ensure_directories(self):
        """確保所需的目錄存在"""
        os.makedirs(self.paths.BASE_DATA_DIR, exist_ok=True)
        os.makedirs(self.paths.EVENT_DIR, exist_ok=True)
        os.makedirs(self.paths.MONTH_DIR, exist_ok=True)
    
    def load_notion_colors(self, property_type: str) -> Dict[str, str]:
        """載入 Notion 顏色配置"""
        try:
            with open(self.paths.SELECT_COLOR_PATH, 'r', encoding='utf-8') as f:
                color_data = json.load(f)
            
            colors = {}
            options = color_data.get(property_type, {}).get('options', [])
            for option in options:
                notion_color = option['color']
                colors[option['name']] = NOTION_TO_MPL_COLORS.get(notion_color, '#37352F')
            
            return colors
        except Exception as e:
            print(f"載入顏色配置時發生錯誤: {e}")
            return {}
    
    def merge_small_portions(self, expenses: Dict[str, float]) -> Dict[str, Any]:
        """合併小於閾值的部分"""
        if not expenses:
            return {}
        
        total = sum(v for v in expenses.values() if v > 0)
        if total == 0:
            return {}
        
        merged = {}
        small_items = []
        
        for item, amount in expenses.items():
            if amount / total < self.config.SMALL_PORTION_THRESHOLD:
                small_items.append(f"{item} ({amount:,.0f})")
            else:
                merged[item] = amount
        
        if small_items:
            merged['__merged__'] = {
                'value': sum(v for v in expenses.values() if v/total < self.config.SMALL_PORTION_THRESHOLD),
                'label': '\n'.join(small_items)
            }
        
        return merged
    
    def create_combined_pie_charts(self, attribute_expenses: Dict[str, float], 
                                 category_expenses: Dict[str, float],
                                 attribute_colors: Dict[str, str], 
                                 category_colors: Dict[str, str],
                                 title: str, save_dir: str):
        """創建合併的圓餅圖"""
        print(f"\n正在生成 {save_dir} 圖表：{title}")
        
        attribute_expenses = {k: v for k, v in attribute_expenses.items() if v > 0}
        category_expenses = {k: v for k, v in category_expenses.items() if v > 0}
        
        attribute_expenses = self.merge_small_portions(attribute_expenses)
        category_expenses = self.merge_small_portions(category_expenses)
        
        if not attribute_expenses and not category_expenses:
            print(f"沒有支出數據，跳過生成圖表：{title}")
            return
        
        plt.figure(figsize=(16, 8), facecolor='black')
        
        total_amount = sum(v['value'] if isinstance(v, dict) else v for v in attribute_expenses.values())
        plt.suptitle(f"{title}\n總計：{total_amount:,.0f}", color='white', size=16, y=0.95)
        
        # 屬性圓餅圖
        self._create_pie_chart(attribute_expenses, attribute_colors, 121, "支出屬性分布")
        
        # 類別圓餅圖
        self._create_pie_chart(category_expenses, category_colors, 122, "支出類別分布")
        
        save_path = os.path.join(save_dir, f"{title}.png")
        plt.savefig(save_path, facecolor='black', bbox_inches='tight')
        print(f"已保存圖表：{save_path}")
        plt.close()
    
    def _create_pie_chart(self, expenses: Dict[str, Any], colors: Dict[str, str], 
                         subplot: int, title: str):
        """創建單個圓餅圖"""
        ax = plt.subplot(subplot)
        ax.set_facecolor('black')
        
        labels = []
        sizes = []
        chart_colors = []
        
        for label, value in expenses.items():
            if isinstance(value, dict):
                if value['value'] > 0:
                    labels.append(value['label'])
                    sizes.append(value['value'])
                    chart_colors.append('#808080')
            else:
                if value > 0:
                    labels.append(f"{label} ({value:,.0f})")
                    sizes.append(value)
                    chart_colors.append(colors.get(label, '#808080'))
        
        if sizes:
            wedges, texts, autotexts = ax.pie(sizes, labels=labels, colors=chart_colors,
                                            autopct='%1.1f%%', wedgeprops=dict(edgecolor='black'))
            plt.setp(texts, color='white', size=12)
            plt.setp(autotexts, color='white', size=12)
        
        ax.set_title(title, color='white', size=14, pad=20)

class ChartManager:
    """管理圖表生成的主要類"""
    
    def __init__(self):
        self.config = Config()
        self.paths = Paths()
        self.chart_generator = ChartGenerator(self.config, self.paths)
        self.data = None  # 添加 data 作為實例變量
    
    def load_data(self, source: str = 'affected') -> Tuple[List[Dict], Set[str], Set[str]]:
        """載入數據和配置
        
        Args:
            source: 數據源，可以是 'affected' 或 'full'
            
        Returns:
            Tuple[List[Dict], Set[str], Set[str]]: (數據, 有效屬性集合, 有效類別集合)
        """
        try:
            with open(self.paths.SELECT_COLOR_PATH, 'r', encoding='utf-8') as f:
                color_config = json.load(f)
            
            valid_attributes = {opt['name'] for opt in color_config.get('屬性', {}).get('options', [])}
            valid_categories = {opt['name'] for opt in color_config.get('類別', {}).get('options', [])}
            
            # 根據 source 選擇數據文件
            if source == 'affected':
                data_path = self.paths.AFFECTED_CHARTS_DATA_PATH
                print(f"使用受影響的數據源：{data_path}")
            elif source == 'full':
                data_path = self.paths.FULL_ACCOUNT_DATA_PATH
                print(f"使用完整數據源：{data_path}")
            else:
                raise ValueError(f"不支持的數據源：{source}")
            
            with open(data_path, 'r', encoding='utf-8') as f:
                self.data = json.load(f)  # 保存到實例變量
            
            return self.data, valid_attributes, valid_categories
        except Exception as e:
            print(f"載入數據時發生錯誤: {e}")
            raise
    
    def process_events(self, data: List[Dict], valid_attributes: Set[str], 
                      valid_categories: Set[str], target_events: Set[str] = None):
        """處理事件圖表"""
        print("\n開始處理事件圖表...")
        
        processor = ChartDataProcessor(data, valid_attributes, valid_categories)
        event_data = defaultdict(lambda: {
            'total': {'attribute': defaultdict(float), 'category': defaultdict(float)},
            'ting': {'attribute': defaultdict(float), 'category': defaultdict(float)},
            'feng': {'attribute': defaultdict(float), 'category': defaultdict(float)}
        })
        
        for record in data:
            event_info = record.get('💥 重大事件支出列表')
            if not event_info:
                continue
            
            event_name = event_info.get('title') if isinstance(event_info, dict) else str(event_info)
            if not event_name:
                continue
                
            # 如果指定了 target_events，只處理這些事件
            if target_events is not None and event_name not in target_events:
                continue
            
            expense = processor.get_expense_amount(record)
            if expense:
                self._process_record_expenses(record, event_data[event_name], processor)
        
        self._generate_event_charts(event_data)
    
    def process_months(self, data: List[Dict], valid_attributes: Set[str], 
                      valid_categories: Set[str], target_months: Set[str] = None):
        """處理月份圖表"""
        print("\n開始處理月份支出圖表...")
        
        processor = ChartDataProcessor(data, valid_attributes, valid_categories)
        month_data = defaultdict(lambda: {
            'total': {'attribute': defaultdict(float), 'category': defaultdict(float)},
            'ting': {'attribute': defaultdict(float), 'category': defaultdict(float)},
            'feng': {'attribute': defaultdict(float), 'category': defaultdict(float)}
        })
        
        # 如果指定了 target_months，只處理這些月份
        if target_months:
            print(f"只處理指定月份：{', '.join(target_months)}")
            month_titles = target_months
        else:
            # 否則收集所有月份
            month_titles = set()
            for record in data:
                month_info = record.get('💵 單月支出列表')
                if not month_info:
                    continue
                
                month_title = month_info.get('title') if isinstance(month_info, dict) else str(month_info)
                if month_title:
                    month_titles.add(month_title)
            
            print(f"找到 {len(month_titles)} 個月份記錄")
            print("月份列表:")
            for title in sorted(month_titles):
                print(f"- {title}")
        
        # 只處理指定的月份
        for record in data:
            month_info = record.get('💵 單月支出列表')
            if not month_info:
                continue
            
            month_title = month_info.get('title') if isinstance(month_info, dict) else str(month_info)
            if not month_title or month_title not in month_titles:
                continue
            
            expense = processor.get_expense_amount(record)
            if expense:
                self._process_record_expenses(record, month_data[month_title], processor)
        
        self._generate_month_charts(month_data)
    
    def _process_record_expenses(self, record: Dict, data_dict: Dict, processor: ChartDataProcessor):
        """處理單條記錄的支出"""
        expense = processor.get_expense_amount(record)
        
        # 處理總支出
        attribute = record.get('屬性')
        if attribute and attribute in processor.valid_attributes:
            data_dict['total']['attribute'][attribute] += expense
        
        category = record.get('類別')
        if category and category in processor.valid_categories:
            data_dict['total']['category'][category] += expense
        
        # 處理個人支出
        ting_exp, feng_exp = processor.process_expenses_by_person(record)
        for attr, amount in ting_exp['attribute'].items():
            data_dict['ting']['attribute'][attr] += amount
        for cat, amount in ting_exp['category'].items():
            data_dict['ting']['category'][cat] += amount
        
        for attr, amount in feng_exp['attribute'].items():
            data_dict['feng']['attribute'][attr] += amount
        for cat, amount in feng_exp['category'].items():
            data_dict['feng']['category'][cat] += amount
    
    def _generate_event_charts(self, event_data: Dict):
        """生成事件圖表"""
        attribute_colors = self.chart_generator.load_notion_colors('屬性')
        category_colors = self.chart_generator.load_notion_colors('類別')
        
        for event_name, expenses in event_data.items():
            if event_name and any(expenses.values()):
                date_range = self._get_event_date_range(event_name)
                base_title = f"{event_name}{date_range}"
                
                self._create_all_pie_charts(
                    expenses['total'],
                    expenses['ting'],
                    expenses['feng'],
                    attribute_colors,
                    category_colors,
                    base_title,
                    self.paths.EVENT_DIR
                )
    
    def _generate_month_charts(self, month_data: Dict):
        """生成月份圖表"""
        attribute_colors = self.chart_generator.load_notion_colors('屬性')
        category_colors = self.chart_generator.load_notion_colors('類別')
        
        month_titles = sorted(month_data.keys())
        print(f"找到 {len(month_titles)} 個月份記錄")
        print("月份列表:")
        for title in month_titles:
            print(f"- {title}")
        
        for month_title in month_titles:
            try:
                self._create_all_pie_charts(
                    month_data[month_title]['total'],
                    month_data[month_title]['ting'],
                    month_data[month_title]['feng'],
                    attribute_colors,
                    category_colors,
                    month_title,
                    self.paths.MONTH_DIR
                )
            except Exception as e:
                print(f"處理月份 {month_title} 時發生錯誤: {str(e)}")
                import traceback
                traceback.print_exc()
    
    def _create_all_pie_charts(self, total_expenses: Dict, ting_expenses: Dict,
                             feng_expenses: Dict, attribute_colors: Dict[str, str],
                             category_colors: Dict[str, str], base_title: str,
                             save_dir: str):
        """為同一組數據創建三種圓餅圖"""
        self.chart_generator.create_combined_pie_charts(
            total_expenses['attribute'],
            total_expenses['category'],
            attribute_colors,
            category_colors,
            base_title,
            save_dir
        )
        
        self.chart_generator.create_combined_pie_charts(
            ting_expenses['attribute'],
            ting_expenses['category'],
            attribute_colors,
            category_colors,
            f"{base_title} (廷)",
            save_dir
        )
        
        self.chart_generator.create_combined_pie_charts(
            feng_expenses['attribute'],
            feng_expenses['category'],
            attribute_colors,
            category_colors,
            f"{base_title} (雰)",
            save_dir
        )
    
    def _get_event_date_range(self, event_name: str) -> str:
        """獲取事件的日期範圍"""
        dates = []
        for record in self.data:
            if record.get('💥 重大事件支出列表') == event_name:
                date = record.get('日期')
                if date and isinstance(date, str):
                    dates.append(date)
        
        if not dates:
            return ""
        
        dates.sort()
        start_date = dates[0]
        end_date = dates[-1]
        
        return f" ({start_date})" if start_date == end_date else f" ({start_date} - {end_date})"
    
    def draw_graph(self, target_events: Set[str] = None, source: str = 'affected'):
        """主要執行函數
        
        Args:
            target_events: 需要處理的事件集合
            source: 數據源，可以是 'affected' 或 'full'
        """
        try:
            data, valid_attributes, valid_categories = self.load_data(source)
            print(f"總記錄數: {len(data)}")
            
            if target_events:
                # 區分事件和月份
                events = {event for event in target_events if '月' not in event}
                months = {event for event in target_events if '月' in event}
                
                if events:
                    print(f"處理事件：{', '.join(events)}")
                    self.process_events(data, valid_attributes, valid_categories, events)
                
                if months:
                    print(f"處理月份：{', '.join(months)}")
                    self.process_months(data, valid_attributes, valid_categories, months)
            else:
                # 如果沒有指定事件，處理所有
                self.process_events(data, valid_attributes, valid_categories)
                self.process_months(data, valid_attributes, valid_categories)
            
        except Exception as e:
            print(f"執行過程中發生錯誤: {str(e)}")
            print(f"錯誤類型: {type(e)}")
            import traceback
            traceback.print_exc()

def main():
    """主函數"""
    chart_manager = ChartManager()
    target_events = {"2025, 04月<<"}#, "菲律賓馬尼拉-墨寶沙丁魚風暴【2025_0308-0316】", "埔里施家莊園2d【2025_0404-05】"}
    #target_events = {}
    chart_manager.draw_graph(target_events, source='affected')  # source='affected'使用受影響的數據源

if __name__ == "__main__":
    main()