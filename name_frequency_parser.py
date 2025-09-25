"""
Name Frequency Parser

This module provides functionality to parse and process name-frequency data from structured strings.
The expected format is: "name1:time1:freq1;name2:time2:freq2;..."

Author: Generated from user code
Date: 2025-09-25
"""

import re
import pandas as pd
from typing import Optional, List, Dict, Any


def _normalize(s: str) -> str:
    """
    Normalize string by replacing Chinese punctuation and standardizing separators.
    
    Args:
        s: Input string to normalize
        
    Returns:
        Normalized string with standardized separators
    """
    if s is None:
        return ""
    s = str(s)
    # Replace Chinese punctuation with English equivalents
    s = s.replace("；", ";").replace("：", ":")
    # Normalize spacing around separators
    s = re.sub(r"\s*;\s*", ";", s.strip())
    s = re.sub(r"\s*:\s*", ":", s)
    return s


def _to_int_or_none(x: str) -> Optional[int]:
    """
    Extract integer from string, return None if no integer found.
    
    Args:
        x: Input string
        
    Returns:
        Extracted integer or None if not found
    """
    if x is None:
        return None
    m = re.search(r"-?\d+", str(x))
    return int(m.group(0)) if m else None


def _parse_token_strict(tok: str) -> Optional[Dict[str, Any]]:
    """
    Parse a single token in format "name:time:frequency".
    
    Args:
        tok: Token string to parse
        
    Returns:
        Dictionary with parsed data or None if invalid format
    """
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
    
    if f is None:  # Frequency must be parseable
        return None
    
    return {"name": _name, "time": t, "freq": f}


def _parse_name_field(cell: str) -> List[Dict[str, Any]]:
    """
    Parse name field containing multiple name:time:frequency entries.
    
    Args:
        cell: Cell content to parse
        
    Returns:
        List of parsed name-time-frequency dictionaries
    """
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


def _time_value(t) -> int:
    """
    Convert time value for comparison. Missing times are treated as very early.
    
    Args:
        t: Time value
        
    Returns:
        Integer value for comparison (higher = more recent)
    """
    return t if isinstance(t, int) else -10**18


def _guess_id_col(df: pd.DataFrame) -> str:
    """
    Attempt to automatically detect ID column from common names.
    
    Args:
        df: DataFrame to analyze
        
    Returns:
        Name of the ID column
        
    Raises:
        KeyError: If no ID column is found
    """
    for c in ["id", "ID", "Id", "IDCard", "idcard", "uuid", "idcard_md5"]:
        if c in df.columns:
            return c
    raise KeyError(f"找不到 id 列，请传入 id_col 参数。可用列：{list(df.columns)}")


def explode_name_frequency(
    df: pd.DataFrame,
    name_col: str = "name_output",
    id_col: Optional[str] = None,
    dedup_by_name: bool = True,
    keep_time: bool = False,
    drop_empty: bool = False
) -> pd.DataFrame:
    """
    Parse and explode name-frequency data from structured strings.
    
    This function takes a DataFrame with name-frequency data in a specific format
    and explodes it into individual rows for each name-frequency pair.
    
    Args:
        df: Input DataFrame
        name_col: Column containing name-frequency data to parse
        id_col: ID column name (auto-detected if None)
        dedup_by_name: Whether to deduplicate by name (keeping highest frequency)
        keep_time: Whether to include time column in output
        drop_empty: Whether to drop rows with no parseable data
        
    Returns:
        DataFrame with exploded name-frequency data
        
    Raises:
        KeyError: If required columns are missing
        
    Example:
        >>> df = pd.DataFrame({
        ...     'id': [1, 2],
        ...     'name_output': ['张三:2023:5;李四:2022:3', '王五:2024:8']
        ... })
        >>> result = explode_name_frequency(df)
        >>> print(result)
           id name_output  frequency
        0   1        张三          5
        1   1        李四          3
        2   2        王五          8
    """
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
                if keep_time:
                    base["time"] = pd.NA
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

        # Sort by frequency (desc), then time (desc), then name (asc)
        items_sorted = sorted(
            items,
            key=lambda d: (-int(d.get("freq", 0)), -_time_value(d.get("time")), str(d.get("name")))
        )

        # Output top 2 results
        for rank, it in enumerate(items_sorted[:2], 1):
            row = {
                id_col: idv,
                "name_output": it["name"],
                "frequency": int(it["freq"]),
            }
            if keep_time:
                row["time"] = it["time"] if it["time"] is not None else pd.NA
            rows.append(row)

    out = pd.DataFrame(rows)
    
    # Ensure consistent column order
    cols = [id_col, "name_output", "frequency"]
    if keep_time:
        cols.append("time")
    
    return out[cols] if not out.empty else out


if __name__ == "__main__":
    # Example usage
    sample_data = pd.DataFrame({
        'id': [1, 2, 3],
        'name_output': [
            '张三:2023:5;李四:2022:3;王五:2024:2',
            '赵六:2023:10;孙七:2022:1',
            '周八:2024:7'
        ]
    })
    
    print("Original data:")
    print(sample_data)
    print("\nProcessed data:")
    result = explode_name_frequency(sample_data, keep_time=True)
    print(result)