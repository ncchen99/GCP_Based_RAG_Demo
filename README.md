# GCP Based RAG Demo 🚀

這是一個基於 Goole Cloud Platform (GCP) 的檢索增強生成系統 (Retrieval-Augmented Generation, RAG)，支援使用 BigQuery 或 Vertex AI Vector Search 作為向量資料庫，並使用 Claude 3.5 作為生成模型。 🤖

## 1. 系統概述 ✨

### 1.1 功能特點
- 🌏 支援中英文雙語檢索
- 🧮 使用 Google Cloud 的文本嵌入模型生成向量
- 🔍 提供兩種向量搜尋方式：
  - BigQuery 向量相似度搜尋
  - Vertex AI Vector Search
- 🤖 使用 Claude 3.5 進行回答生成
- 🕷️ 支援將 GPT-Crawler 爬取的資料轉換為向量資料

### 1.2 技術選擇比較 ⚖️

#### 1.2.1 BigQuery 優勢 💪
- 🏃‍♂️ 無需額外部署，可立即使用
- 💰 成本較低，按查詢計費
- 🔄 可與現有的 SQL 查詢整合
- 🛠️ 維護成本低，無需管理基礎設施

#### 1.2.2 Vector Search 優勢 💫
- ⚡ 查詢速度更快，特別是大規模資料集
- 🎯 更精確的向量相似度搜尋
- 🔍 支援更多相似度計算方法
- 📈 可擴展性更好

#### 1.2.3 成本考量 💰
- Vector Search：
  - 需要持續運行的執行個體
  - 建立索引時需要計算資源
  - Google 目前提供 $1,000 USD (約 NT$30,000) 免費額度
  - 建議從小規模開始，根據需求擴展

- BigQuery：
  - 按查詢資料量計費
  - 無需額外基礎設施成本
  - 適合中小規模應用

#### 1.2.4 選擇建議 🤔
1. 小規模應用（<100萬筆資料）：
   - 👉 選擇 BigQuery
   - 成本效益更好
   - 設置簡單

2. 大規模應用（>100萬筆資料）：
   - 👉 選擇 Vector Search
   - 更好的查詢效能
   - 可根據負載自動擴展

## 2. 開始使用 📋

### 2.1 前置需求
1. 🌐 Google Cloud Platform 帳號與專案
2. ⚙️ 以下 API 需要啟用：
   - BigQuery API
   - Vertex AI API
   - Cloud Storage API
   - Cloud Translation API
3. 🐍 Python 3.8+
4. 📦 必要的 Python 套件：
```bash
pip install -r requirements.txt
```

### 2.2 環境設置 🔐

創建 `.env` 檔案並設置以下變數：
```env
GOOGLE_APPLICATION_CREDENTIALS=/path/to/your/service-account-key.json
ANTHROPIC_API_KEY=your_anthropic_api_key
```

### 2.3 資料準備 🔢

如果你有使用 GPT-Crawler 爬取的資料（JSON 格式），請按照以下步驟處理：

1. 生成向量嵌入：
```bash
python misc/generate_embeddings.py \
  --input_file your_crawler_data.json \
  --output_file combined_embeddings.json
```

2. 轉換為 JSONL 格式：
```bash
python misc/convert_to_jsonl.py \
  --input_file combined_embeddings.json \
  --output_file combined_embeddings.jsonl
```

## 3. 系統設置 🛠️

### 3.1 Vector Search 設置

1. 🔍 進入 Vertex AI > Vector Search
2. 🆕 點擊「Create Index」
3. ⚙️ 設置索引參數：
   - Display name: 為索引命名
   - Dimensions: 設置向量維度（例如：768）
   - Approximate neighbors count: 設置近似鄰居數量（例如：10）
   - Distance measure: 選擇距離計算方式（建議：Cosine Distance）
   - Algorithm config: 選擇演算法配置（建議：Tree-AH）
4. 📤 上傳向量資料：
   - 選擇已上傳到 Cloud Storage 的 JSONL 檔案
   - 等待索引建立（可能需要 30-60 分鐘）
5. 🚀 部署索引：
   - 建立 Index Endpoint
   - 將索引部署到端點
   - 選擇機器類型和節點數量

### 3.2 BigQuery 設置

1. 創建 Cloud Storage bucket：
```bash
gsutil mb -l us-central1 gs://your-bucket-name
```

2. 上傳 JSONL 檔案：
```bash
gsutil cp combined_embeddings.jsonl gs://your-bucket-name/
```

3. 建立資料表：
```bash
bq mk --location=us-central1 your_dataset_name
```

4. 創建資料表結構：
```sql
CREATE TABLE `your_project.your_dataset.your_table`
(
  id STRING,
  title STRING,
  url STRING,
  content STRING,
  embedding ARRAY<FLOAT64>
);
```

5. 載入資料：
```bash
bq load \
  --source_format=NEWLINE_DELIMITED_JSON \
  your_dataset.your_table \
  gs://your-bucket-name/combined_embeddings.jsonl \
  id:STRING,title:STRING,url:STRING,content:STRING,embedding:FLOAT64
```

## 4. 使用說明 🎯

### 4.1 使用 BigQuery 版本
```bash
python rag_big_query.py
```

### 4.2 使用 Vector Search 版本
```bash
python rag_vector_search.py
```

## 5. 專案結構 📁

```
.
├── README.md
├── requirements.txt
├── .env
├── rag_big_query.py          # 使用 BigQuery 的 RAG 實現
├── rag_vector_search.py      # 使用 Vector Search 的 RAG 實現
└── misc/
    ├── generate_embeddings.py    # 生成向量嵌入
    └── convert_to_jsonl.py       # 轉換 JSON 到 JSONL 格式
```

## 6. 注意事項 ⚠️

1. 🔑 確保你的 GCP 服務帳號具有足夠的權限
2. 📍 Vector Search 和 BigQuery 的位置必須在同一區域
3. 🌎 建議使用 `us-central1` 作為主要區域
4. 🔒 檢查 Cloud Storage bucket 和資料表的存取權限設置

## 7. 常見問題 ❓

1. 如果遇到權限問題，請檢查：
   - 🔐 服務帳號的權限設置
   - ✅ API 是否已啟用
   - 🆔 專案 ID 是否正確

2. 如果向量搜尋結果不理想：
   - 🎯 調整 `num_neighbors` 參數
   - 📏 檢查向量維度是否正確
   - 🤔 確認嵌入模型的選擇是否適當

## 8. 貢獻指南 🤝

歡迎提交 Issue 和 Pull Request！ 💖

## 9. 授權 📜

MIT License

