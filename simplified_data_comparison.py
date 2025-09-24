# -*- coding: utf-8 -*-
"""
简化版数据对比脚本
功能：对比线上和线下两个CSV文件中的异常数据
作者：为Python初学者优化
"""

import pandas as pd
from pathlib import Path

# ===========================================
# 第一步：设置文件路径
# ===========================================
# 请根据你的实际情况修改这些路径
online_file = r"D:\测试文件\纳知\测试文件集合\二要素核验测试\mobile-id 二要素测试\返回文件\明文样本查询结果\线上线下核验结果\核对_score_输出\线上测试核验样本解析.csv"
offline_file = r"D:\测试文件\纳知\测试文件集合\二要素核验测试\mobile-id 二要素测试\返回文件\明文样本查询结果\处理匹配好的文件\raw_sample_107.csv"
output_file = r"D:\测试文件\纳知\测试文件集合\二要素核验测试\mobile-id 二要素测试\返回文件\明文样本查询结果\处理匹配好的文件\核对线上线下查无样本.csv"

print("开始处理数据...")

# ===========================================
# 第二步：读取CSV文件（自动处理编码问题）
# ===========================================
def read_csv_file(file_path):
    """
    读取CSV文件，自动尝试不同编码
    """
    encodings = ['utf-8-sig', 'utf-8', 'gb18030', 'gbk', 'latin1']
    
    for encoding in encodings:
        try:
            df = pd.read_csv(file_path, dtype=str, encoding=encoding, low_memory=False)
            print(f"成功读取文件：{Path(file_path).name}（编码：{encoding}）")
            return df
        except:
            continue
    
    raise Exception(f"无法读取文件：{file_path}")

# 读取两个文件
online_data = read_csv_file(online_file)
offline_data = read_csv_file(offline_file)

print(f"线上数据行数：{len(online_data)}")
print(f"线下数据行数：{len(offline_data)}")

# ===========================================
# 第三步：找到需要的列
# ===========================================
def find_column(dataframe, possible_names):
    """
    在数据框中查找可能的列名
    """
    # 将所有列名转换为小写，便于匹配
    columns_lower = {col.lower(): col for col in dataframe.columns}
    
    for name in possible_names:
        if name.lower() in columns_lower:
            return columns_lower[name.lower()]
    
    raise Exception(f"找不到列，可能的列名：{possible_names}")

# 查找身份证列
id_possible_names = ['id', '身份证', '身份证号', 'idcard', 'id_card', '证件号']
online_id_col = find_column(online_data, id_possible_names)
offline_id_col = find_column(offline_data, id_possible_names)

# 查找手机号列
phone_possible_names = ['phone', 'mobile', '手机号', '手机']
online_phone_col = find_column(online_data, phone_possible_names)
offline_phone_col = find_column(offline_data, phone_possible_names)

# 查找线上状态列（billStatus）
bill_status_names = ['billstatus', 'bill_status']
online_status_col = find_column(online_data, bill_status_names)

# 查找线下状态列（包含"要素不一致"、"查无"等）
offline_status_col = None
for col in offline_data.columns:
    # 检查这一列是否包含我们要找的关键词
    sample_data = offline_data[col].astype(str)
    if sample_data.str.contains('要素不一致|要素不匹配|查无', na=False).sum() > 0:
        offline_status_col = col
        break

if offline_status_col is None:
    raise Exception("找不到包含'要素不一致'、'要素不匹配'或'查无'的列")

print(f"找到的列名：")
print(f"  线上身份证列：{online_id_col}")
print(f"  线上手机号列：{online_phone_col}")
print(f"  线上状态列：{online_status_col}")
print(f"  线下身份证列：{offline_id_col}")
print(f"  线下手机号列：{offline_phone_col}")
print(f"  线下状态列：{offline_status_col}")

# ===========================================
# 第四步：筛选异常数据
# ===========================================
# 筛选线上数据：只要 billStatus = -1 的记录
online_abnormal = online_data[
    online_data[online_status_col].astype(str).str.strip() == '-1'
].copy()

# 筛选线下数据：只要包含"要素不一致"、"要素不匹配"或"查无"的记录
offline_abnormal = offline_data[
    offline_data[offline_status_col].astype(str).str.contains('要素不一致|要素不匹配|查无', na=False)
].copy()

print(f"线上异常数据：{len(online_abnormal)} 条")
print(f"线下异常数据：{len(offline_abnormal)} 条")

# ===========================================
# 第五步：数据清理和标准化
# ===========================================
# 创建统一的标识键（身份证+手机号）
online_abnormal['标识键'] = (
    online_abnormal[online_id_col].astype(str).str.strip() + '_' + 
    online_abnormal[online_phone_col].astype(str).str.strip()
)

offline_abnormal['标识键'] = (
    offline_abnormal[offline_id_col].astype(str).str.strip() + '_' + 
    offline_abnormal[offline_phone_col].astype(str).str.strip()
)

# 去除重复数据
online_abnormal = online_abnormal.drop_duplicates(subset=['标识键'], keep='first')
offline_abnormal = offline_abnormal.drop_duplicates(subset=['标识键'], keep='first')

print(f"去重后 - 线上异常数据：{len(online_abnormal)} 条")
print(f"去重后 - 线下异常数据：{len(offline_abnormal)} 条")

# ===========================================
# 第六步：数据对比
# ===========================================
# 准备用于合并的数据
online_for_merge = online_abnormal[['标识键', online_id_col, online_phone_col, online_status_col]].copy()
offline_for_merge = offline_abnormal[['标识键', offline_id_col, offline_phone_col, offline_status_col]].copy()

# 重命名列，便于后续处理
online_for_merge.columns = ['标识键', '身份证', '手机号', '线上状态']
offline_for_merge.columns = ['标识键', '身份证', '手机号', '线下状态']

# 外连接合并数据
merged_data = pd.merge(
    online_for_merge, 
    offline_for_merge, 
    on='标识键', 
    how='outer', 
    suffixes=('_线上', '_线下')
)

# ===========================================
# 第七步：添加对比标签
# ===========================================
def get_comparison_label(row):
    """
    根据数据来源给出对比标签
    """
    has_online = pd.notna(row['线上状态']) and row['线上状态'] != ''
    has_offline = pd.notna(row['线下状态']) and row['线下状态'] != ''
    
    if has_online and has_offline:
        return "两边都异常"
    elif has_online:
        return "仅线上异常"
    elif has_offline:
        return "仅线下异常"
    else:
        return "未知情况"

merged_data['对比结果'] = merged_data.apply(get_comparison_label, axis=1)

# 整理最终输出的列
# 优先使用有数据的身份证和手机号
merged_data['最终身份证'] = merged_data['身份证_线上'].fillna(merged_data['身份证_线下'])
merged_data['最终手机号'] = merged_data['手机号_线上'].fillna(merged_data['手机号_线下'])

# ===========================================
# 第八步：生成结果报告
# ===========================================
# 统计各类情况的数量
both_count = len(merged_data[merged_data['对比结果'] == '两边都异常'])
online_only_count = len(merged_data[merged_data['对比结果'] == '仅线上异常'])
offline_only_count = len(merged_data[merged_data['对比结果'] == '仅线下异常'])

print("\n=== 对比结果统计 ===")
print(f"两边都异常：{both_count} 条")
print(f"仅线上异常：{online_only_count} 条")
print(f"仅线下异常：{offline_only_count} 条")
print(f"总计：{len(merged_data)} 条")

# ===========================================
# 第九步：保存结果
# ===========================================
# 选择要输出的列
output_columns = [
    '最终身份证', '最终手机号', '线上状态', '线下状态', '对比结果'
]

final_result = merged_data[output_columns].copy()

# 重命名列，让输出更清晰
final_result.columns = ['身份证', '手机号', '线上状态', '线下状态', '对比结果']

# 保存到CSV文件
Path(output_file).parent.mkdir(parents=True, exist_ok=True)
final_result.to_csv(output_file, index=False, encoding='utf-8-sig')

print(f"\n结果已保存到：{output_file}")
print("处理完成！")