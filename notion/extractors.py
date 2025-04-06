from .config import NotionConfig
class PropertyValueExtractor:
    @staticmethod
    def extract_rollup_value(rollup_data: dict) -> any:
        """提取 rollup 屬性的值"""
        rollup_type = rollup_data.get('type')
        if not rollup_type:
            return None

        value = rollup_data.get(rollup_type)
        if not value:
            return None

        # 根據不同的 rollup 類型處理值
        if rollup_type in ['number', 'date']:
            return value
        elif rollup_type == 'array':
            # 處理數組類型的 rollup
            return [PropertyValueExtractor.extract_value(item) for item in value]
        elif rollup_type == 'unsupported':
            return None
        
        return value

    @staticmethod
    def format_date_range(date_value):
        """格式化日期範圍
        
        格式規則：
        1. 同年份：yyyy_mmdd-mmdd
        2. 跨年份：yyyy_mmdd-yyyy_mmdd
        """
        if not date_value:
            return None
            
        start = date_value.get('start')
        end = date_value.get('end')
        
        if not start:
            return None
            
        # 解析開始和結束日期
        start_parts = start.split('-')
        start_year = start_parts[0]
        start_month = start_parts[1].zfill(2)
        start_day = start_parts[2].zfill(2)
        
        if not end:
            return f"{start_year}_{start_month}{start_day}"
            
        end_parts = end.split('-')
        end_year = end_parts[0]
        end_month = end_parts[1].zfill(2)
        end_day = end_parts[2].zfill(2)
        
        # 如果是同一年
        if start_year == end_year:
            # 如果是同一月份且結束日期小於10，只顯示日期數字
            if start_month == end_month and int(end_day) < 10:
                return f"{start_year}_{start_month}{start_day}-{end_day}"
            # 否則顯示完整月日
            return f"{start_year}_{start_month}{start_day}-{end_month}{end_day}"
        else:
            # 跨年份則完整顯示
            return f"{start_year}_{start_month}{start_day}-{end_year}_{end_month}{end_day}"

    @staticmethod
    def extract_value(property_data: dict) -> any:
        """統一的屬性值提取方法"""
        prop_type = property_data.get('type')
        if not prop_type:
            return None

        extractors = {
            NotionConfig.PropertyType.TITLE: lambda x: x['title'][0]['text']['content'] if x['title'] else '',
            NotionConfig.PropertyType.RICH_TEXT: lambda x: x['rich_text'][0]['text']['content'] if x['rich_text'] else '',
            NotionConfig.PropertyType.NUMBER: lambda x: x['number'],
            NotionConfig.PropertyType.SELECT: lambda x: x['select']['name'] if x['select'] else '',
            NotionConfig.PropertyType.MULTI_SELECT: lambda x: [option['name'] for option in x['multi_select']],
            NotionConfig.PropertyType.DATE: lambda x: PropertyValueExtractor.format_date_range(x['date']),
            NotionConfig.PropertyType.CHECKBOX: lambda x: x['checkbox'],
            NotionConfig.PropertyType.URL: lambda x: x['url'],
            NotionConfig.PropertyType.EMAIL: lambda x: x['email'],
            NotionConfig.PropertyType.PHONE: lambda x: x['phone_number'],
            NotionConfig.PropertyType.RELATION: lambda x: [rel['id'] for rel in x['relation']],
            NotionConfig.PropertyType.ROLLUP: lambda x: PropertyValueExtractor.extract_rollup_value(x['rollup'])
        }

        extractor = extractors.get(prop_type)
        return extractor(property_data) if extractor else property_data[prop_type]
