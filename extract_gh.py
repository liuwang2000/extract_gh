import argparse
import re
import os
import shutil
import shlex
from datetime import datetime
import sys

class Color:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

def get_user_input():
    parser = argparse.ArgumentParser(description='GH家族序列提取工具')
    parser.add_argument('--anno', help='注释文件路径')
    parser.add_argument('--faa', help='蛋白序列文件路径')
    parser.add_argument('--ffn', help='核酸序列文件路径')
    parser.add_argument('--keywords', nargs='+', help='搜索关键词列表')
    
    args = parser.parse_args()
    
    # 交互式输入未提供的参数
    if not args.anno:
        args.anno = input("请输入anno文件路径: ").strip()
    if not args.faa:
        args.faa = input("请输入faa文件路径: ").strip()
    if not args.ffn:
        args.ffn = input("请输入ffn文件路径: ").strip()
    if not args.keywords:
        input_keywords = input("请输入搜索关键词(多个用空格分隔，可使用引号包裹含空格的词组): ").strip()
        args.keywords = shlex.split(input_keywords)
    
    return args

def build_regex_pattern(keywords):
    patterns = []
    for kw in keywords:
        # 标准化输入格式
        kw = re.sub(r'\s+', ' ', kw)  # 合并多余空格
        # 构建精确匹配模式
        pattern = r'\b' + re.sub(
            r'[\\s_-]+', 
            r'[\\s_-]+', 
            re.escape(kw.lower())
        ) + r'\b'
        patterns.append(pattern)
    
    combined = '|'.join(patterns)
    return fr'(?i){combined}'  # 不区分大小写

def process_files(args):
    # 文件验证
    for f in [args.anno, args.faa, args.ffn]:
        if not os.path.exists(f):
            print(f"{Color.FAIL}错误：文件 {f} 不存在{Color.ENDC}")
            sys.exit(1)

    # 创建带时间戳的输出目录
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = f"{os.path.splitext(os.path.basename(args.anno))[0]}_output_{timestamp}"
    os.makedirs(output_dir, exist_ok=True)

    # 构建正则表达式
    pattern = build_regex_pattern(args.keywords)
    regex = re.compile(pattern, flags=re.IGNORECASE)

    # 处理注释文件
    unique_ids = set()
    with open(args.anno, 'r') as f_in:
        for line in f_in:
            if regex.search(line):
                parts = line.split('\t')
                gene_id = parts[0].split()[0]
                if gene_id not in unique_ids:
                    unique_ids.add(gene_id)

    if not unique_ids:
        print(f"{Color.WARNING}警告: 未找到有效序列！{Color.ENDC}")
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir, ignore_errors=True)
        else:
            print(f"{Color.WARNING}警告: 输出目录未创建{Color.ENDC}")
        sys.exit(0)

    # 写入过滤后的注释文件
    with open(args.anno, 'r') as f_in, \
         open(os.path.join(output_dir, 'filtered.anno'), 'w') as f_out:
        
        for line in f_in:
            parts = line.split('\t')
            if len(parts) < 2:
                continue
            # 仅在注释字段（第二列）匹配
            if regex.search(parts[1]):
                gene_id = parts[0].strip()
                if gene_id in unique_ids:  # 只写入已收集的基因ID
                    f_out.write(line)

    # 提取序列函数
    def extract_sequences(input_file, output_file, ids):
        writing = False
        with open(input_file, 'r') as f_in, \
             open(output_file, 'w') as f_out:
            for line in f_in:
                if line.startswith('>'):
                    current_id = line.split()[0][1:]
                    writing = current_id in ids
                if writing:
                    f_out.write(line)

    # 提取序列
    extract_sequences(args.faa, os.path.join(output_dir, 'output.faa'), unique_ids)
    extract_sequences(args.ffn, os.path.join(output_dir, 'output.ffn'), unique_ids)

    # 结果处理
    # 结果处理保留（已前置检查）

    # 动态生成文件名
    match_count = len(unique_ids)
    base_name = os.path.splitext(os.path.basename(args.anno))[0]
    output_prefix = f"{base_name}_matches_{match_count}"

    # 重命名输出文件
    os.rename(os.path.join(output_dir, 'filtered.anno'), os.path.join(output_dir, f"{output_prefix}.anno"))
    os.rename(os.path.join(output_dir, 'output.faa'), os.path.join(output_dir, f"{output_prefix}.faa"))
    os.rename(os.path.join(output_dir, 'output.ffn'), os.path.join(output_dir, f"{output_prefix}.ffn"))

    # 生成报告
    report = f'''=== 筛选报告 ===
输入文件: {os.path.basename(args.anno)}
匹配关键词: {', '.join(args.keywords)}
有效匹配: {match_count}
输出文件:
  - {output_prefix}.anno
  - {output_prefix}.faa
  - {output_prefix}.ffn
执行时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
'''
    with open(os.path.join(output_dir, 'report.txt'), 'w', encoding='utf-8') as f:
        f.write(report)

    # 文件验证
    for ext in ['faa', 'ffn']:
        file_path = os.path.join(output_dir, f"{output_prefix}.{ext}")
        if os.path.getsize(file_path) == 0:
            print(f"{Color.FAIL}错误：{ext.upper()}序列文件为空！{Color.ENDC}")
            sys.exit(1)

    print(f"{Color.OKGREEN}处理完成！输出文件：{Color.ENDC}")
    print(f"{Color.OKBLUE}» {output_prefix}.anno")
    print(f"» {output_prefix}.faa")
    print(f"» {output_prefix}.ffn{Color.ENDC}")

if __name__ == "__main__":
    args = get_user_input()
    try:
        process_files(args)
    except Exception as e:
        print(f"{Color.FAIL}错误发生: {str(e)}{Color.ENDC}")
        sys.exit(1)