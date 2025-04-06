# Notion 賬戶圖表生成系統

這是一個用於從 Notion 數據庫中提取數據並生成圖表的 Python 系統。系統可以自動從 Notion 賬戶數據庫中獲取支出記錄，生成圓餅圖，並將圖表更新到對應的 Notion 頁面中。

## 功能特點

- **自動數據同步**：自動從 Notion 數據庫獲取最新的支出記錄
- **智能圖表生成**：
  - 支持生成總支出圓餅圖
  - 支持生成個人支出圓餅圖（廷/雰）
  - 自動處理圖表更新和版本控制
- **圖片管理**：
  - 自動上傳圖表到 Imgur
  - 智能管理圖片記錄
  - 避免重複上傳
- **靈活的配置**：
  - 支持多個數據庫配置
  - 可配置的圖表生成選項
  - 環境變量支持

## 系統要求

- Python 3.6+
- Notion API 訪問權限
- Imgur API 訪問權限

## 安裝步驟

1. 克隆倉庫：
```bash
git clone git@github.com:robinkct/notion_account_graph.git
cd notion_account_graph
```

2. 複製配置文件：
```bash
cp secrets.py.example secrets.py
```

3. 編輯 `secrets.py`，填入您的 Notion API 配置：
```python
NOTION_TOKEN = 'your_notion_token_here'
NOTION_ACCOUNT_DB_ID = 'your_account_database_id'
NOTION_EVENT_DB_ID = 'your_event_database_id'
NOTION_MONTH_DB_ID = 'your_month_database_id'
```

## 使用方法

### 基本使用

運行主程序：
```bash
python money.py
```

### 重繪特定圖表

要重繪特定事件的圖表，修改 `money.py` 中的 `titles_to_redraw` 列表：
```python
titles_to_redraw = ["2025, 01月", "2025, 02月"]  # 設置要重繪的標題
```

## 目錄結構

```
notion_account_graph/
├── data/               # 數據存儲目錄
│   └── image/         # 圖片存儲目錄
│       ├── event/     # 事件圖表
│       └── month/     # 月度圖表
├── examples/          # 示例代碼
├── notion/           # Notion API 相關代碼
├── money.py          # 主程序
├── draw_graph.py     # 圖表生成模塊
├── secrets.py        # 配置文件（需要自行創建）
└── secrets.py.example # 配置文件模板
```

## 主要功能模塊

### 數據處理
- 從 Notion 獲取支出記錄
- 處理數據關聯
- 生成圖表數據

### 圖表生成
- 生成總支出圓餅圖
- 生成個人支出圓餅圖
- 自動更新圖表

### 圖片管理
- 自動上傳到 Imgur
- 管理圖片記錄
- 版本控制

## 注意事項

1. 請確保 `secrets.py` 中的配置正確
2. 不要將 `secrets.py` 提交到版本控制系統
3. 定期備份數據目錄

## 開發計劃

- [ ] 添加更多圖表類型
- [ ] 優化圖片上傳機制
- [ ] 添加數據導出功能
- [ ] 改進錯誤處理

## 貢獻指南

歡迎提交 Issue 和 Pull Request 來幫助改進這個項目。

## 許可證

MIT License
