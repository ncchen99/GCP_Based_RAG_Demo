import os
import json
from google.cloud import aiplatform
from vertexai.language_models import TextEmbeddingModel

def load_json_files(json_files):
    """
    載入多個 JSON 檔案並合併其內容。
    
    Args:
        json_files (list): JSON 檔案的路徑列表。
        
    Returns:
        list: 合併後的所有條目列表。
    """
    all_entries = []
    for file in json_files:
        with open(file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # 為每個條目添加來源資訊
            for entry in data:
                entry['source_file'] = os.path.basename(file)
            all_entries.extend(data)
    return all_entries

def generate_text_embeddings(texts, model_name="text-multilingual-embedding-002"):
    """
    使用 Vertex AI 的嵌入模型生成文本向量。
    
    Args:
        texts (list): 要生成嵌入的文本列表。
        model_name (str): 使用的嵌入模型名稱。
        
    Returns:
        list: 嵌入向量的列表。
    """
    # 初始化 Vertex AI
    aiplatform.init(
        project="eros-ai-446307",  # 替換為您的 GCP 專案 ID
        location="us-central1"      # 替換為您的模型所在區域
    )

    # 載入嵌入模型
    model = TextEmbeddingModel.from_pretrained(model_name)
    
    # Vertex AI 每次預測最多允許 250 個實例
    max_batch_size = 5
    embeddings = []

    # 將 texts 分批處理
    for i in range(0, len(texts), max_batch_size):
        print(f"Processing batch {i // max_batch_size + 1} of {len(texts) // max_batch_size}")
        batch_texts = texts[i:i + max_batch_size]
        batch_embeddings = model.get_embeddings(batch_texts)
        embeddings.extend([embedding.values for embedding in batch_embeddings])

    return embeddings

def generate_embeddings_json(json_files, output_json, model_name="text-multilingual-embedding-002"):
    """
    從指定的 JSON 檔案生成一個包含嵌入向量的 JSON 檔案。
    
    Args:
        json_files (list): 要處理的 JSON 檔案列表。
        output_json (str): 輸出的 JSON 檔案名稱。
        model_name (str): 使用的嵌入模型名稱。
    """
    embeddings = []
    # 載入所有 JSON 檔案
    all_entries = load_json_files(json_files)
    
    # 提取所有文本內容以批量生成嵌入
    all_texts = [entry.get("html", "") for entry in all_entries]
    file_ids = [entry.get("url", "") for entry in all_entries]  # 使用 URL 作為 ID

    # 生成嵌入向量
    embedding_vectors = generate_text_embeddings(all_texts, model_name=model_name)

    # 組織嵌入資料
    for doc_id, embedding, entry in zip(file_ids, embedding_vectors, all_entries):
        embeddings.append({
            "id": doc_id,  # 使用 URL 作為唯一標識符
            "title": entry.get("title", ""),
            "url": entry.get("url", ""),
            "content": entry.get("html", ""),
            "embedding": embedding
        })

    # 將結果寫入 JSON 檔案
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(embeddings, f, ensure_ascii=False, indent=4)

    print(f"已成功生成 {output_json}，包含 {len(embeddings)} 條記錄。")

if __name__ == "__main__":
    # 指定要處理的 JSON 檔案
    json_files = [
        "./helloclue.com.json",
        "./scarleteen.com.json",
        "./talk.yiwu.io.json"
    ]
    output_json = "combined_embeddings.json"  # 輸出 JSON 檔案名稱
    model_name = "text-multilingual-embedding-002"  # Vertex AI 嵌入模型名稱

    generate_embeddings_json(json_files, output_json, model_name) 