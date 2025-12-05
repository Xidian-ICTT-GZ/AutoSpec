import json
import os
import re

# ================= 配置区域 =================
INPUT_FILE = "/app/terminates_check/31_verified_files/verification_results.jsonl"

OUTPUT_FILE = "/app/terminates_check/31_verified_files/verification_results_sorted.jsonl"
# ===========================================

def get_file_number(entry):
    """
    从 entry 中提取 file_name 的数字部分用于排序。
    例如: {"file_name": "27.c", ...} -> 返回整数 27
    """
    filename = entry.get("file_name", "")
    
    # 使用正则提取文件名中的数字
    # 匹配文件名开头的一个或多个数字
    match = re.match(r'(\d+)', filename)
    
    if match:
        return int(match.group(1))
    else:
        # 如果文件名不包含数字（例如 error.c），返回无穷大，让它排在最后
        return float('inf')

def main():
    # 1. 检查输入文件是否存在
    if not os.path.exists(INPUT_FILE):
        print(f"错误: 找不到文件 {INPUT_FILE}")
        return

    print(f"正在读取 {INPUT_FILE} ...")
    
    data_lines = []
    
    # 2. 读取并解析每一行 JSON
    try:
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line: # 跳过空行
                    try:
                        json_obj = json.loads(line)
                        data_lines.append(json_obj)
                    except json.JSONDecodeError:
                        print(f"警告: 跳过无法解析的行: {line}")
    except Exception as e:
        print(f"读取出错: {e}")
        return

    print(f"共读取 {len(data_lines)} 条记录。正在排序...")

    # 3. 核心排序逻辑
    # key 参数指定用什么值来比较。我们使用 get_file_number 函数提取的整数。
    # 这样 "27.c" (27) 就会排在 "114.c" (114) 前面。
    data_lines.sort(key=get_file_number)

    # 4. 写入新文件
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            for entry in data_lines:
                # ensure_ascii=False 保证如果里面有中文也能正常显示
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')
        
        print(f"排序完成！结果已保存至: {OUTPUT_FILE}")
        
        # 打印前几条看看效果
        print("-" * 20)
        print("排序后预览 (前 5 条):")
        for i, entry in enumerate(data_lines[:5]):
            print(json.dumps(entry))
            
    except Exception as e:
        print(f"写入出错: {e}")

if __name__ == "__main__":
    main()