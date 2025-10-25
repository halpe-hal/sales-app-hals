# modules/utils.py

import jpholiday
from datetime import datetime

# --- 祝日 or 土日 判定 ---
def is_holiday_or_weekend(date_obj):
    """渡された日付が土日または祝日ならTrue"""
    return date_obj.weekday() >= 5 or jpholiday.is_holiday(date_obj)

# --- 安全なint変換（DB読み込み時などに使う） ---
def safe_convert_to_int(x):
    """intに安全変換する。bytes型にも対応。"""
    try:
        if isinstance(x, bytes):
            return int.from_bytes(x, byteorder='little')
        elif x is not None:
            return int(x)
        else:
            return 0
    except:
        return 0

# --- 日付文字列（YYYY-MM-DD）をdatetimeに安全変換 ---
def safe_str_to_date(date_str):
    """文字列→datetime変換（失敗しても落ちない）"""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except Exception:
        return None
