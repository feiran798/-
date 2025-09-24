# ===== 单元格1：导入库和设置路径 =====
import pandas as pd
from pathlib import Path

# 设置文件路径（请根据你的实际路径修改）
online_file = r"D:\测试文件\纳知\测试文件集合\二要素核验测试\mobile-id 二要素测试\返回文件\明文样本查询结果\线上线下核验结果\核对_score_输出\线上测试核验样本解析.csv"
raw_file = r"D:\测试文件\纳知\测试文件集合\二要素核验测试\mobile-id 二要素测试\返回文件\明文样本查询结果\处理匹配好的文件\raw_sample_107.csv"

# 输出文件路径
output_file = Path(raw_file).parent / "核对线上线下查无样本.csv"

print("文件路径设置完成！")

# ===== 单元格2：读取CSV文件的函数 =====
def read_csv_file(file_path):
    """尝试用不同编码读取CSV文件"""
    encodings = ["utf-8-sig", "utf-8", "gb18030", "gbk"]
    
    for encoding in encodings:
        try:
            print(f"尝试用 {encoding} 编码读取...")
            df = pd.read_csv(file_path, encoding=encoding, dtype=str)
            print(f"成功！用 {encoding} 编码读取了 {len(df)} 行数据")
            return df
        except:
            continue
    
    print(f"错误：无法读取文件 {file_path}")
    return None

# ===== 单元格3：读取数据文件 =====
# 读取线上数据
print("正在读取线上数据...")
df_online = read_csv_file(online_file)

# 读取线下数据
print("\n正在读取线下数据...")
df_raw = read_csv_file(raw_file)

# 检查读取结果
if df_online is not None and df_raw is not None:
    print(f"\n数据读取成功！")
    print(f"线上数据：{len(df_online)} 行，{len(df_online.columns)} 列")
    print(f"线下数据：{len(df_raw)} 行，{len(df_raw.columns)} 列")
else:
    print("数据读取失败，请检查文件路径")

# ===== 单元格4：查找数据列的函数 =====
def find_column(df, possible_names, description):
    """在数据框中查找指定列"""
    for name in possible_names:
        for col in df.columns:
            if name.lower() in str(col).lower():
                print(f"找到{description}列：{col}")
                return col
    print(f"错误：未找到{description}列")
    return None

# ===== 单元格5：查找需要的列 =====
print("正在查找数据列...")

# 查找身份证列
id_columns = ["id", "身份证", "身份证号", "idcard", "证件号"]
id_col_online = find_column(df_online, id_columns, "身份证")
id_col_raw = find_column(df_raw, id_columns, "身份证")

# 查找手机号列
phone_columns = ["phone", "mobile", "手机号", "手机"]
phone_col_online = find_column(df_online, phone_columns, "手机号")
phone_col_raw = find_column(df_raw, phone_columns, "手机号")

# 查找状态列
status_col_online = find_column(df_online, ["billstatus", "bill_status"], "线上状态")
status_col_raw = find_column(df_raw, ["要素不一致", "要素不匹配", "查无"], "线下状态")

# 检查是否找到所有必需的列
if all([id_col_online, id_col_raw, phone_col_online, phone_col_raw, status_col_online, status_col_raw]):
    print("\n所有必需的列都已找到！")
else:
    print("\n无法找到所有必需的列，请检查数据文件")

# ===== 单元格6：筛选数据 =====
print("正在筛选数据...")

# 筛选线上数据：billStatus = -1
online_filtered = df_online[df_online[status_col_online].astype(str).str.strip() == "-1"].copy()
print(f"线上异常数据：{len(online_filtered)} 条")

# 筛选线下数据：包含"要素不一致"、"要素不匹配"或"查无"
def contains_error(text):
    error_keywords = ["要素不一致", "要素不匹配", "查无"]
    text_str = str(text).strip()
    return any(keyword in text_str for keyword in error_keywords)

raw_filtered = df_raw[df_raw[status_col_raw].apply(contains_error)].copy()
print(f"线下异常数据：{len(raw_filtered)} 条")

# ===== 单元格7：准备合并数据 =====
print("正在准备合并数据...")

# 选择需要的列
online_data = online_filtered[[id_col_online, phone_col_online, status_col_online]].copy()
raw_data = raw_filtered[[id_col_raw, phone_col_raw, status_col_raw]].copy()

# 重命名列，方便合并
online_data.columns = ["身份证", "手机号", "线上状态"]
raw_data.columns = ["身份证", "手机号", "线下状态"]

# 清理数据（去除空格）
online_data["身份证"] = online_data["身份证"].astype(str).str.strip()
online_data["手机号"] = online_data["手机号"].astype(str).str.strip()
raw_data["身份证"] = raw_data["身份证"].astype(str).str.strip()
raw_data["手机号"] = raw_data["手机号"].astype(str).str.strip()

# 去重
online_data = online_data.drop_duplicates(subset=["身份证", "手机号"])
raw_data = raw_data.drop_duplicates(subset=["身份证", "手机号"])

print(f"去重后 - 线上：{len(online_data)} 条，线下：{len(raw_data)} 条")

# ===== 单元格8：合并数据 =====
print("正在合并数据...")

# 使用外连接合并数据
merged = pd.merge(online_data, raw_data, on=["身份证", "手机号"], how="outer", indicator=True)

# 添加标签
def add_label(row):
    if row["_merge"] == "both":
        return "两边都异常"
    elif row["_merge"] == "left_only":
        return "仅线上异常"
    else:
        return "仅线下异常"

merged["对比结果"] = merged.apply(add_label, axis=1)

# 整理输出列
result = merged[["身份证", "手机号", "线上状态", "线下状态", "对比结果"]].copy()

# 填充空值
result["线上状态"] = result["线上状态"].fillna("")
result["线下状态"] = result["线下状态"].fillna("")

print("数据合并完成！")

# ===== 单元格9：统计和保存结果 =====
print("正在统计结果...")

# 统计各种情况的数量
both_error = len(result[result["对比结果"] == "两边都异常"])
online_only = len(result[result["对比结果"] == "仅线上异常"])
raw_only = len(result[result["对比结果"] == "仅线下异常"])

# 保存结果
result.to_csv(output_file, index=False, encoding="utf-8-sig")

# 显示统计结果
print("\n" + "="*50)
print("分析完成！")
print("="*50)
print(f"总记录数：{len(result)}")
print(f"两边都异常：{both_error} 条")
print(f"仅线上异常：{online_only} 条")
print(f"仅线下异常：{raw_only} 条")
print(f"结果已保存到：{output_file}")
print("="*50)

# ===== 单元格10：查看结果预览 =====
# 显示前几行结果
print("结果预览（前10行）：")
print(result.head(10))

# 显示各类型数据的数量分布
print("\n各类型数据分布：")
print(result["对比结果"].value_counts())