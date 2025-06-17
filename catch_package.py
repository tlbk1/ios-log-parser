import os
import re
import json
import zipfile
import requests
from io import BytesIO

def download_file(url, save_path):
    """下载ZIP文件（增强错误处理和进度提示）"""
    try:
        print(f"开始下载文件: {url}")
        response = requests.get(url, stream=True, timeout=15)
        response.raise_for_status()
        
        # 显示下载进度
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        chunk_size = 8192
        
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    progress = int(100 * downloaded / total_size)
                    print(f"下载进度: {progress}%", end="\r")
        
        print(f"\n✅ 文件下载成功，保存至: {save_path}")
        return save_path
    except requests.Timeout:
        print("\n❌ 下载超时，请检查网络连接")
    except requests.HTTPError as e:
        print(f"\n❌ HTTP错误 {e.response.status_code}")
    except Exception as e:
        print(f"\n❌ 下载失败: {str(e)}")
    return None

def extract_zip(zip_path, extract_dir):
    """解压ZIP文件（支持指定文件夹结构）"""
    try:
        print(f"开始解压文件: {zip_path}")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # 确保目标目录存在
            if not os.path.exists(extract_dir):
                os.makedirs(extract_dir)
            
            # 解压所有文件
            zip_ref.extractall(extract_dir)
        
        print(f"✅ 文件解压成功，目录: {extract_dir}")
        return extract_dir
    except zipfile.BadZipFile:
        print(f"❌ 无效的ZIP文件: {zip_path}")
    except Exception as e:
        print(f"❌ 解压失败: {str(e)}")
    return None

def extract_network_info(txt_file):
    """从TXT文件中提取网络请求/响应信息"""
    network_data = []
    try:
        with open(txt_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # 定义精准的网络信息提取规则
        network_patterns = [
            # 匹配[YFLNetwork]相关的网络请求
            r'\[YFLNetwork\](.*?)\n',
            # 匹配完整的URL
            r'https?://[^\s"\']+',
            # 匹配HTTP状态码
            r'\s(200|301|302|400|401|403|404|500)\s',
            # 匹配JSON格式的响应数据
            r'\{.*?\}'
        ]
        
        # 提取URL和状态码
        urls = re.findall(network_patterns[1], content)
        status_codes = re.findall(network_patterns[2], content)
        
        # 提取[YFLNetwork]模块的详细信息
        yfl_data = re.findall(network_patterns[0], content, re.DOTALL)
        json_data = []
        
        for item in yfl_data:
            # 提取JSON数据
            json_matches = re.findall(network_patterns[3], item)
            for json_str in json_matches:
                try:
                    json_obj = json.loads(json_str)
                    json_data.append(json_obj)
                except:
                    continue
        
        # 整理数据结构
        if urls or status_codes or json_data:
            network_data.append({
                'file': os.path.basename(txt_file),
                'urls': list(set(urls)),  # 去重后限制数量
                'status_codes': list(set(status_codes)),
                'yfl_network': json_data  # 最多提取5条详细数据
            })
    
    except FileNotFoundError:
        print(f"❌ 找不到文件: {txt_file}")
    except Exception as e:
        print(f"❌ 处理文件失败 {txt_file}: {str(e)}")
    
    return network_data

def process_extracted_files(extract_dir):
    """处理解压后的文件，提取TXT中的网络信息"""
    network_data = []
    txt_files = []
    
    # 查找所有TXT文件（支持多级目录）
    for root, _, files in os.walk(extract_dir):
        for file in files:
            if file.endswith('.txt'):
                txt_files.append(os.path.join(root, file))
    
    if not txt_files:
        print("❌ 未找到TXT文件")
        return network_data
    
    print(f"找到 {len(txt_files)} 个TXT文件，开始提取网络信息...")
    
    # 处理每个TXT文件
    for txt_file in txt_files:
        file_data = extract_network_info(txt_file)
        if file_data:
            network_data.extend(file_data)
    
    return network_data

def main():
    """主函数（优化工作流程）"""
    print("=== 网络日志提取工具 ===")
    
    # 获取ZIP文件URL
    log_url = input("请输入ZIP文件下载URL: ").strip()
    if not log_url:
        print("❌ URL不能为空")
        return
    
    # 定义文件路径
    zip_file = "downloaded_log.zip"
    extract_dir = os.path.splitext(zip_file)[0] + "_extracted"
    
    # 下载ZIP文件
    if not download_file(log_url, zip_file):
        return
    
    # 解压ZIP文件
    if not extract_zip(zip_file, extract_dir):
        return
    
    # 处理解压后的文件
    network_data = process_extracted_files(extract_dir)
    
    # 输出结果
    if network_data:
        output_file = "network_analysis.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(network_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 网络数据提取完成，保存至: {output_file}")
        print(f"🔍 共提取 {len(network_data)} 条网络相关记录")
    else:
        print("❌ 未提取到网络请求/响应信息")

if __name__ == "__main__":
    main()