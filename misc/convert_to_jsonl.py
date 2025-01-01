import json

def convert_json_to_jsonl(input_json_path, output_jsonl_path):
    """
    將 JSON 檔案轉換為 JSON Lines 格式。

    Args:
        input_json_path (str): 輸入的 JSON 檔案路徑。
        output_jsonl_path (str): 輸出的 JSONL 檔案路徑。
    """
    try:
        with open(input_json_path, 'r', encoding='utf-8') as infile:
            data = json.load(infile)
        
        with open(output_jsonl_path, 'w', encoding='utf-8') as outfile:
            for entry in data:
                json_line = json.dumps(entry, ensure_ascii=False)
                outfile.write(json_line + '\n')
        
        print(f"成功將 {input_json_path} 轉換為 {output_jsonl_path}。")
    
    except Exception as e:
        print(f"轉換過程中發生錯誤：{e}")

if __name__ == "__main__":
    input_json = "combined_embeddings.json"       # 輸入的 JSON 檔案名稱
    output_jsonl = "combined_embeddings.jsonl"    # 輸出的 JSONL 檔案名稱
    convert_json_to_jsonl(input_json, output_jsonl) 