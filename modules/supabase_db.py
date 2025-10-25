# modules/supabase_db.py（新店舗版：カテゴリなし）

from modules.supabase_client import supabase
from datetime import date

# --- hals_jiyugaoka_salesテーブルの取得 ---
def fetch_sales_data(year=None, month=None):
    from_to_step = 1000  # 一度に取得する件数（Supabase推奨は1000）
    all_data = []
    offset = 0

    while True:
        query = supabase.table("hals_jiyugaoka_sales").select("*").range(offset, offset + from_to_step - 1)

        if year:
            query = query.eq("year", year)
        if month:
            query = query.eq("month", month)

        response = query.execute()
        data = response.data or []
        all_data.extend(data)

        if len(data) < from_to_step:
            break

        offset += from_to_step

    return all_data


# --- hals_jiyugaoka_salesテーブルへの登録・更新（UPSERT） ---
def insert_sales(data):
    for record in data:
        year = record["year"]
        month = record["month"]
        date_str = record["date"]

        existing = supabase.table("hals_jiyugaoka_sales") \
            .select("id") \
            .eq("date", date_str) \
            .execute()

        if existing.data:
            supabase.table("hals_jiyugaoka_sales").update(record).eq("id", existing.data[0]["id"]).execute()
        else:
            record.pop("id", None)
            supabase.table("hals_jiyugaoka_sales").insert(record).execute()


# --- hals_jiyugaoka_salesデータの削除（日付指定） ---
def delete_sales_by_date(date_str):
    response = supabase.table("hals_jiyugaoka_sales") \
        .delete() \
        .eq("date", date_str) \
        .execute()
    return response


# --- hals_jiyugaoka_targetsテーブルの取得 ---
def fetch_targets(year=None, month=None):
    from_to_step = 1000
    all_data = []
    offset = 0

    while True:
        query = supabase.table("hals_jiyugaoka_targets").select("*").range(offset, offset + from_to_step - 1)

        if year:
            query = query.eq("year", year)
        if month:
            query = query.eq("month", month)

        response = query.execute()
        data = response.data or []
        all_data.extend(data)

        if len(data) < from_to_step:
            break

        offset += from_to_step

    return all_data


# --- hals_jiyugaoka_targetsテーブルへの登録・更新（UPSERT） ---
def upsert_target(year, month, date_str, target_sales):
    data = {
        "year": year,
        "month": month,
        "date": date_str,
        "target_sales": target_sales
    }

    existing = supabase.table("hals_jiyugaoka_targets") \
        .select("id") \
        .eq("year", year) \
        .eq("month", month) \
        .eq("date", date_str) \
        .execute()

    if existing.data:
        supabase.table("hals_jiyugaoka_targets").update(data).eq("id", existing.data[0]["id"]).execute()
    else:
        supabase.table("hals_jiyugaoka_targets").insert(data).execute()


# --- hals_jiyugaoka_minimum_targetsの取得 ---
def fetch_minimum_targets():
    response = supabase.table("hals_jiyugaoka_minimum_targets").select("*").order("month", desc=False).execute()
    return response.data


# --- hals_jiyugaoka_minimum_targetsへの登録・更新 ---
def insert_minimum_target(month, min_sales):
    response = supabase.table("hals_jiyugaoka_minimum_targets").upsert([
        {"month": month, "min_sales": min_sales}
    ]).execute()
    return response


# --- 売上データの範囲取得（日付指定） ---
def fetch_sales_data_range(start_date, end_date):
    res = supabase.table("hals_jiyugaoka_sales") \
        .select("*") \
        .gte("date", start_date.strftime("%Y-%m-%d")) \
        .lte("date", end_date.strftime("%Y-%m-%d")) \
        .execute()
    return res.data or []


# --- 目標データの範囲取得（日付指定） ---
def fetch_targets_in_range(start_date, end_date):
    res = supabase.table("hals_jiyugaoka_targets") \
        .select("*") \
        .gte("date", start_date.strftime("%Y-%m-%d")) \
        .lte("date", end_date.strftime("%Y-%m-%d")) \
        .execute()
    return res.data or []
