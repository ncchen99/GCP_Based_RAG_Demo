import os
import json
from dotenv import load_dotenv
from google.cloud import bigquery
from vertexai.language_models import TextEmbeddingModel
import anthropic
from google.cloud import translate_v2 as translate

def load_query_embedding(query, model_name="text-multilingual-embedding-002"):
    """
    使用 Vertex AI 嵌入模型將查詢轉換為向量。
    
    Args:
        query (str): 用戶的查詢。
        model_name (str): 嵌入模型名稱。
        
    Returns:
        list: 查詢的嵌入向量。
    """
    import vertexai
    vertexai.init(project="eros-ai-446307", location="us-central1")
    
    model = TextEmbeddingModel.from_pretrained(model_name)
    embeddings = model.get_embeddings([query])
    return embeddings[0].values

def retrieve_similar_documents(query_embedding, dataset_id, table_id, project_id, top_n=10):
    """
    使用 BigQuery 查找與查詢向量相似的文檔。
    
    Args:
        query_embedding (list): 查詢的嵌入向量。
        dataset_id (str): BigQuery 資料集 ID。
        table_id (str): BigQuery 資料表 ID。
        project_id (str): GCP 專案 ID。
        top_n (int): 返回的相似文檔數量。
        
    Returns:
        list: 相似文檔的列表。
    """
    client = bigquery.Client(project=project_id)
    
    # 將查詢向量轉換為字符串格式
    embedding_str = ", ".join(map(str, query_embedding))
    
    # 創建 SQL 查詢，使用表別名來避免欄位名稱模糊
    query = f"""
    WITH query AS (
      SELECT
        [{embedding_str}] AS embedding
    )
    
    SELECT
      t.id,
      t.title,
      t.url,
      t.content,
      t.embedding,
      (
        (SELECT SUM(q * d) 
         FROM UNNEST(qry.embedding) AS q WITH OFFSET i 
         JOIN UNNEST(t.embedding) AS d WITH OFFSET j 
         ON i = j)
        /
        (SQRT((SELECT SUM(POWER(q, 2)) FROM UNNEST(qry.embedding) AS q)) * 
         SQRT((SELECT SUM(POWER(d, 2)) FROM UNNEST(t.embedding) AS d)))
      ) AS cosine_similarity
    FROM
      `{project_id}.{dataset_id}.{table_id}` AS t,
      query AS qry
    ORDER BY
      cosine_similarity DESC
    LIMIT {top_n}
    """
    
    query_job = client.query(query)
    results = query_job.result()
    
    documents = []
    for row in results:
        documents.append({
            "id": row.id,
            "title": row.title,
            "url": row.url,
            "content": row.content,
            "cosine_similarity": row.cosine_similarity
        })
    
    return documents

def translate_text(text):
    """
    使用 Google Translate API 將文本翻譯為英文。
    
    Args:
        text (str): 原始文本（中文）。
        
    Returns:
        str: 翻譯後的英文文本。
    """
    translate_client = translate.Client()

    try:
        result = translate_client.translate(text, target_language='en')
        return result['translatedText']
    except Exception as e:
        print(f"翻譯失敗：{str(e)}")
        return ""

def generate_response(documents_cn, documents_en, user_query, claude_client, model):
    """
    使用檢索到的中英文文檔與用戶查詢生成回答。
    
    Args:
        documents_cn (list): 中文檢索到的文檔列表。
        documents_en (list): 英文檢索到的文檔列表。
        user_query (str): 用戶的查詢。
        claude_client: Anthropic 的 API 客戶端。
        model (str): Anthropic 模型名稱。
        
    Returns:
        str: 生成的回答。
    """
    try:
        combined_context = "\n\n".join([doc["content"] for doc in documents_cn + documents_en])
        prompt = f"""上下文信息：
{combined_context}

用戶問題：
{user_query}

回答："""


        # 使用 Anthropic API 進行回答
        message = claude_client.messages.create(
            model=model,
            max_tokens=8192,
            temperature=0.6,  # 調整此處的 temperature
            system="""你是一個飽學性知識的專家，負責與用戶真誠的聊天。 過程要保持熱情、友善且具有同理心。""",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
         
        
        
        return message.content[0].text

    except Exception as e:
        print(f"生成回答時發生錯誤：{str(e)}")
        return ""

if __name__ == "__main__":
    # 載入環境變數
    load_dotenv()
     
    # 從環境變數獲取 Anthropic API 金鑰
    ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
    if not ANTHROPIC_API_KEY:
        raise ValueError("未設置 ANTHROPIC_API_KEY 環境變數")
    
    MODEL = "claude-3-5-sonnet-20241022"  # 替換為您使用的模型名稱
    
    # 初始化 Anthropic client
    claude_client = anthropic.Anthropic(
        api_key=ANTHROPIC_API_KEY,
    )
    
    # 用戶查詢
    user_query = input("請輸入查詢：")
    
    # 使用 Claude 翻譯查詢為英文
    translated_query = translate_text(user_query)
    print("\n翻譯後的英文查詢：")
    print(translated_query)
    print("\n" + "="*50 + "\n")
    
    # 加載中文查詢嵌入
    query_embedding_cn = load_query_embedding(user_query)
    
    # 加載英文查詢嵌入
    query_embedding_en = load_query_embedding(translated_query)
    
    # 檢索相似中文文檔
    dataset_id = "Eros_AI_RAG"
    table_id = "combined_embeddings"
    project_id = "eros-ai-446307"
    similar_docs_cn = retrieve_similar_documents(query_embedding_cn, dataset_id, table_id, project_id, top_n=2)
    
    # 檢索相似英文文檔
    similar_docs_en = retrieve_similar_documents(query_embedding_en, dataset_id, table_id, project_id, top_n=3)
    
    print(similar_docs_cn)
    print(similar_docs_en)
    
    # 生成回答，整合中英文文獻
    answer = generate_response(similar_docs_cn, similar_docs_en, user_query, claude_client, MODEL)
    
    print("生成的回答：")
    print(answer) 
    print("\n" + "="*50 + "\n")