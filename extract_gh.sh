#!/bin/bash
# 用法: ./extract_gh.sh <combined_prefix> <search_pattern>
# 示例:
#   ./extract_gh.sh eryuan_single_1 'GH10|Glyco_hydro_10'
#   不带创建者: ./extract_gh10_final.sh 300gMore100

# 参数检查
if [ $# -lt 2 ]; then
    echo "Usage: $0 <combined_prefix> <search_pattern>"
    echo "示例: $0 eryuan_single_1 'GH10|Glyco_hydro_10'"
    exit 1
fi

# 基础参数解析
COMBINED_PREFIX="$1"

# 基础参数接收
COMBINED_PREFIX="$1"
a="${2#More}"  # 直接获取第二个参数的数字部分

# 输入文件验证
ANN_FILE="${COMBINED_PREFIX}.anno"
FAA_FILE="${COMBINED_PREFIX}.faa"
FFN_FILE="${COMBINED_PREFIX}.ffn"
for f in "$ANN_FILE" "$FAA_FILE" "$FFN_FILE"; do
    [ -f "$f" ] || { echo "缺失文件: $f"; exit 1; }
done

# 创建输出目录
OUTPUT_DIR="${COMBINED_PREFIX}_gh10_output"
mkdir -p "$OUTPUT_DIR" || { echo "目录创建失败"; exit 1; }

# 精准搜索模式
pattern="$2"
# 新增关键词参数检查
if [ $# -lt 2 ]; then
    echo "Usage: $0 <combined_prefix> <keywords>"
    echo "示例: $0 blz_a4_300gMore100 'GH10|Glyco_hydro_10'"
    exit 1
fi

# 生成注释文件（严格去重）
grep -i -w -E "$pattern" "$ANN_FILE" | 
awk -F'\t' '!seen[$1]++' > "${OUTPUT_DIR}/tmp.anno"

# 提取有效ID列表（兼容FASTA头中的额外信息）
cut -f1 "${OUTPUT_DIR}/tmp.anno" | cut -d ' ' -f1 | sort | uniq > "${OUTPUT_DIR}/ids.txt"

# 统计匹配数
match_count=$(wc -l < "${OUTPUT_DIR}/ids.txt")

# 结果处理
if [ "$match_count" -gt 0 ]; then
    # 动态生成文件名
    output_basename="${COMBINED_PREFIX}_matches_${match_count}"

    # 提取序列
    seqkit grep -j 4 -f "${OUTPUT_DIR}/ids.txt" \
        "$FAA_FILE" > "${OUTPUT_DIR}/${output_basename}.faa"
  
    seqkit grep -j 4 -f "${OUTPUT_DIR}/ids.txt" \
        "$FFN_FILE" > "${OUTPUT_DIR}/${output_basename}.ffn"
  
    # 重命名注释文件
    mv "${OUTPUT_DIR}/tmp.anno" "${OUTPUT_DIR}/${output_basename}.anno"
  
    # 生成报告
    {
        echo "=== GH筛选报告 ==="
        
        echo "输入文件: ${COMBINED_PREFIX}"
        echo "有效匹配: ${match_count}"
        echo "匹配关键词: $2"
echo "执行时间: $(date +"%Y-%m-%d %H:%M:%S")"
    } > "${OUTPUT_DIR}/report.txt"
  
    # 验证输出文件非空
    [ -s "${OUTPUT_DIR}/${output_basename}.faa" ] || { echo "错误：蛋白序列文件为空！"; exit 1; }
    [ -s "${OUTPUT_DIR}/${output_basename}.ffn" ] || { echo "错误：核酸序列文件为空！"; exit 1; }
else
    echo "警告: 未找到有效GH序列！"
    rm -rf "$OUTPUT_DIR"
    exit 0
fi

# 清理临时文件
rm -f "${OUTPUT_DIR}/ids.txt"

echo "处理完成！输出文件结构:"
tree -h "$OUTPUT_DIR"
