import re
import pandas as pd

# —— 统一分隔符/空格 ——
def _normalize(s: str) -> str:
    if s is None:
        return ""
    s = str(s)
    s = s.replace("；", ";").replace("：", ":")
    s = re.sub(r"\s*;\s*", ";", s.strip())
    s = re.sub(r"\s*:\s*", ":", s)
    return s

# —— 提取整数（失败返回 None）——
def _to_int_or_none(x: str):
    if x is None:
        return None
    m = re.search(r"-?\d+", str(x))
    return int(m.group(0)) if m else None

# —— 严格解析一个 token：name:时间:频次 -> {'name','time','freq'} —— 
def _parse_token_strict(tok: str):
    parts = tok.split(":")
    if len(parts) < 3:
        return None
    _name = parts[0].strip()
    _time_raw = parts[1].strip()
    _freq_raw = parts[2].strip()
    if not _name:
        return None
    t = _to_int_or_none(_time_raw)
    f = _to_int_or_none(_freq_raw)
    if f is None:   # 频次必须可解析
        return None
    return {"name": _name, "time": t, "freq": f}

# —— 解析 Name 字段，仅接受 name:时间:频次 —— 
def _parse_name_field(cell: str):
    s = _normalize(cell)
    if not s:
        return []
    toks = [t for t in s.split(";") if t]
    out = []
    for t in toks:
        item = _parse_token_strict(t)
        if item is not None:
            out.append(item)
    return out

# —— 时间比较：更"近"即数值更大；若缺失则视为很早 —— 
def _time_value(t):
    return t if isinstance(t, int) else -10**18

def _guess_id_col(df: pd.DataFrame):
    for c in ["id", "ID", "Id", "IDCard", "idcard", "uuid","idcard_md5"]:
        if c in df.columns:
            return c
    raise KeyError("找不到 id 列，请传入 id_col 参数（例如 id/IDCard/uuid 等）")

def explode_name_frequency(
    df: pd.DataFrame,
    name_col: str = "name_output",   # ✅ 用 name_output 作为解析源
    id_col: str | None = None,
    dedup_by_name: bool = True,
    keep_time: bool = False,
    drop_empty: bool = False         # ✅ 先置 False，方便排查
) -> pd.DataFrame:
    if id_col is None:
        id_col = _guess_id_col(df)
    need_cols = [id_col, name_col]
    missing = [c for c in need_cols if c not in df.columns]
    if missing:
        raise KeyError(f"缺少列：{missing}；当前可用列：{list(df.columns)}")

    rows = []
    for _, r in df[need_cols].iterrows():
        idv = r[id_col]
        items = _parse_name_field(r[name_col])

        if not items:
            if not drop_empty:
                base = {id_col: idv, "name_output": pd.NA, "frequency": pd.NA}
                if keep_time: base["time"] = pd.NA
                rows.append(base)
            continue

        if dedup_by_name:
            best = {}
            for it in items:
                nm = it["name"]
                prev = best.get(nm)
                if (prev is None) or (it["freq"] > prev["freq"]) or (
                    it["freq"] == prev["freq"] and _time_value(it["time"]) > _time_value(prev["time"])
                ):
                    best[nm] = it
            items = list(best.values())

        items_sorted = sorted(
            items,
            key=lambda d: (-int(d.get("freq", 0)), -_time_value(d.get("time")), str(d.get("name")))
        )

        # ✅ 仅输出 Top1/Top2，并保持列名：name_output / frequency
        for rank, it in enumerate(items_sorted[:2], 1):
            row = {
                id_col: idv,
                "name_output": it["name"],          # ✅ 修正为 name_output
                "frequency": int(it["freq"]),
            }
            if keep_time:
                row["time"] = it["time"] if it["time"] is not None else pd.NA
            rows.append(row)

    out = pd.DataFrame(rows)
    cols = [id_col, "name_output", "frequency"] + (["time"] if keep_time else [])
    return out[cols] if not out.empty else out