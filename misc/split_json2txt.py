import json
import re
import os

def extract_id(url, domain):
    """
    根據不同的域名提取主題 ID，如果沒有數字 ID，則使用標題中的關鍵詞。
    """
    if 'talk.yiwu.io' in domain:
        match = re.search(r'/t/topic/(\d+)', url)
        if match:
            return match.group(1)
    elif 'scarleteen.com' in domain:
        match = re.search(r'/read/.+/(.+)\?page=', url)
        if match:
            return match.group(1)
    elif 'helloclue.com' in domain:
        match = re.search(r'/articles/.+/(.+)', url)
        if match:
            return match.group(1)
    # 如果沒有匹配，使用 URL 中的最後一部分作為 ID
    return url.rstrip('/').split('/')[-1]

def split_json_to_txt(input_file, output_dir):
    """
    將大的 JSON 檔案拆分成多個小的 .txt 檔案。

    :param input_file: 輸入的 JSON 檔案路徑
    :param output_dir: 輸出的資料夾路徑
    """
    # 確保輸出資料夾存在
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 讀取 JSON 檔案
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 遍歷每個主題
    for item in data:
        title = item.get('title', 'No Title')
        url = item.get('url', 'No URL')
        html = item.get('html', 'No Content')

        # 獲取域名
        domain_match = re.search(r'https?://([^/]+)/', url)
        domain = domain_match.group(1) if domain_match else 'unknown'

        # 提取 ID
        topic_id = extract_id(url, domain)
        if not topic_id:
            print(f"無法從網址中提取 ID: {url}")
            continue

        # 定義輸出檔案名稱
        # 將域名中的點替換為下劃線，以避免檔案名中的點造成混淆
        domain_safe = domain.replace('.', '_')
        output_filename = f"{domain_safe}.{topic_id}.txt"
        output_path = os.path.join(output_dir, output_filename)

        # 編寫內容到 .txt 檔案
        with open(output_path, 'w', encoding='utf-8') as out_file:
            out_file.write(f"title: \n{title}\n")
            out_file.write(f"url: {url}\n")
            out_file.write(f"html: \n{html}\n")

        print(f"已創建檔案: {output_path}")

# 使用範例
if __name__ == "__main__":
    # 定義輸入的 JSON 檔案和輸出資料夾
    input_json_files = ['talk.yiwu.io.txt', 'scarleteen.com.txt', 'helloclue.com.txt']
    output_directory = 'split_txt_files'

    for json_file in input_json_files:
        split_json_to_txt(json_file, output_directory)
