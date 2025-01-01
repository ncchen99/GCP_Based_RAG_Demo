import json
import os
import requests
import time
from dotenv import load_dotenv
from vertexai.language_models import TextEmbeddingModel
from google.cloud import aiplatform
import anthropic

def load_embeddings(file_path):
    """載入向量檔案"""
    embeddings = None
    with open(file_path, 'r', encoding='utf-8') as f:
        embeddings = json.loads(f.read())  # 將每行的 JSON 對象載入
    return embeddings

def generate_text_embeddings(text) -> list:    
    """生成文本向量"""
    model = TextEmbeddingModel.from_pretrained("text-multilingual-embedding-002")
    embeddings = model.get_embeddings([text])
    return [embedding.values for embedding in embeddings]

def generate_context(ids, embeddings_data):
    """根據 ID 生成上下文"""
    context = []
    for id in ids:
        for entry in embeddings_data:
            if entry['id'] == id:
                context.append({
                    'title': entry.get('title', ''),
                    'url': entry.get('url', ''),
                    'content': entry.get('content', '')
                })
    return context

def format_context(context_items):
    """格式化上下文為易讀格式"""
    formatted_text = ""
    for item in context_items:
        formatted_text += f"標題: {item['title']}\n"
        formatted_text += f"來源: {item['url']}\n"
        formatted_text += f"內容:\n{item['content']}\n\n"
    return formatted_text.strip()

def main():
    # 載入環境變數
    load_dotenv()
    
    # 從環境變數獲取 Anthropic API 金鑰
    ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
    if not ANTHROPIC_API_KEY:
        raise ValueError("未設置 ANTHROPIC_API_KEY 環境變數")
    
    MODEL = "claude-3-5-sonnet-20241022"  # 替換為您使用的模型名稱
    
    # 初始化 Anthropic client
    client = anthropic.Anthropic(
        # 默認從環境變數中讀取 "ANTHROPIC_API_KEY"
        api_key=ANTHROPIC_API_KEY,
    )
    
    # 設置專案資訊
    PROJECT_ID = "eros-ai-446307"
    LOCATION = "us-central1"
    
    # 初始化 Vertex AI（僅用於向量搜尋）
    aiplatform.init(
        project=PROJECT_ID,
        location=LOCATION,
        encryption_spec_key_name=None
    )
    
    # 載入向量資料
    embeddings_data = load_embeddings("combined_embeddings.json")
    
    
    # 取得索引端點
    index_endpoint = aiplatform.MatchingEngineIndexEndpoint(
        index_endpoint_name=f"projects/{PROJECT_ID}/locations/{LOCATION}/indexEndpoints/6993135845213470720"
    )
    
    while True:
        # 獲取用戶輸入
        query = input("請輸入你的問題 (輸入 'quit' 結束): ")
        if query.lower() == 'quit':
            break
        
        print("搜尋相關內容...")
        
        # 生成查詢向量
        query_embedding = generate_text_embeddings(query)
        
        # 搜尋相似文檔
        response = index_endpoint.find_neighbors(
            deployed_index_id="eros_search_node_1735580001214",
            queries=[query_embedding[0]],
            num_neighbors=5
        )
        
        # 獲取相似文檔 ID
        matching_ids = [neighbor.id for sublist in response for neighbor in sublist]
        
        print(matching_ids)
        
        # 生成上下文
        context_items = generate_context(matching_ids, embeddings_data)
        
        print(context_items)
        
        formatted_context = format_context(context_items)
        
        print(formatted_context)
        
        # 使用 Anthropic API 進行回答
        try:
            message = client.messages.create(
                model=MODEL,
                max_tokens=8192,
                temperature=0.6,  # 調整此處的 temperature
                system="""你是一個飽學性知識的專家，負責與用戶真誠的聊天。 過程要保持熱情、友善且具有同理心。""",
                messages=[
                    {
                        "role": "user",
                        "content": f"""上下文信息：
{formatted_context}

用戶問題：
{query}

"""
                    }
                ]
            )
            
            # 輸出回答
            print("\n回答：")
            print(message.content[0].text)
            print("\n" + "="*50 + "\n")
            
        except Exception as e:
            print(f"發生錯誤：{str(e)}")

if __name__ == "__main__":
    main()