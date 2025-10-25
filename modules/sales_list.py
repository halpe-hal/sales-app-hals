# modules/sales_input.py（新店舗版）

import streamlit as st
import pandas as pd
import math
import io
from datetime import datetime
import jpholiday
from modules import supabase_db as db
from modules import utils

def show():
    st.markdown("<h2>売上入力フォーム</h2>", unsafe_allow_html=True)

    today = datetime.today()
    input_date = st.date_input("日付を選択してください", value=today, format="YYYY/MM/DD")

    date_str = input_date.strftime('%Y-%m-%d')
    year = input_date.year
    month = input_date.month

    targets = db.fetch_targets(year, month)
    target_sales = 0
    for row in targets:
        if row["date"] == date_str:
            target_sales = row["target_sales"]

    existing_sales = db.fetch_sales_data(year, month)
    already_exists = any(row["date"] == date_str for row in existing_sales)

    # --- 売上入力フォーム ---
    with st.form("sales_form"):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            store_sales = st.number_input("店舗売上 (円)", min_value=0, step=1000, value=None, placeholder="必須")
        with col2:
            delivery_sales = st.number_input("デリバリー売上 (円)", min_value=0, step=1000, value=None, placeholder="任意")
        with col3:
            other_sales = st.number_input("その他売上 (円)", min_value=0, step=1000, value=None, placeholder="任意")
        with col4:
            customer_count = st.number_input("客数", min_value=0, step=1, value=None, placeholder="必須")

        store_val = store_sales or 0
        delivery_val = delivery_sales or 0
        other_val = other_sales or 0
        actual_sales = store_val + delivery_val + other_val
        unit_price = store_sales / customer_count if store_sales and customer_count else 0

        if store_sales and customer_count:
            st.markdown(f"**自動計算：客単価 = ¥{unit_price:.0f}**")

        if target_sales:
            st.markdown(f"**目標売上：¥{int(target_sales):,}**")
        else:
            st.warning("⚠️ この日の売上目標が未設定です。")

        col_space, col_submit = st.columns([9, 1])
        with col_submit:
            submitted = st.form_submit_button("保存")

    if submitted:
        if store_sales is None or customer_count is None:
            st.error("❌ 店舗売上と客数は必須項目です。")
        elif already_exists:
            st.error(f"{input_date.strftime('%Y/%m/%d')} の売上は既に入力されています")
        else:
            db.insert_sales([{
                "year": year,
                "month": month,
                "date": date_str,
                "store_sales": store_val,
                "delivery_sales": delivery_val,
                "other_sales": other_val,
                "actual_sales": actual_sales,
                "customer_count": customer_count,
                "unit_price": unit_price
            }])
            st.success("保存しました！")
            st.rerun()

    # --- CSVアップロード ---
    with st.expander("売上CSVアップロード"):
        st.markdown("CSV形式：**日付,店舗売上,デリバリー売上,その他売上,客数**")
        uploaded_file = st.file_uploader("CSVファイルを選択", type=["csv"])
        if uploaded_file:
            try:
                df_upload = pd.read_csv(uploaded_file, encoding="utf-8")
                st.dataframe(df_upload)
            except Exception as e:
                st.error(f"CSV読み込みエラー: {e}")
                return

            def parse_int_field(value):
                try:
                    return int(str(value).replace(",", "").strip())
                except:
                    return 0

            if st.button("データベースに保存する"):
                records = []
                for _, row in df_upload.iterrows():
                    try:
                        date_str = pd.to_datetime(row["日付"]).strftime("%Y-%m-%d")
                        year = pd.to_datetime(row["日付"]).year
                        month = pd.to_datetime(row["日付"]).month
                        store = parse_int_field(row["店舗売上"])
                        delivery = parse_int_field(row["デリバリー売上"])
                        other = parse_int_field(row["その他売上"])
                        cust = parse_int_field(row["客数"])
                        actual = store + delivery + other
                        unit_price = store / cust if cust else 0

                        records.append({
                            "year": year, "month": month, "date": date_str,
                            "store_sales": store, "delivery_sales": delivery,
                            "other_sales": other, "actual_sales": actual,
                            "customer_count": cust, "unit_price": unit_price
                        })
                    except Exception as e:
                        st.error(f"行エラー: {e}")
                        continue

                db.insert_sales(records)
                st.success(f"{len(records)}件の売上データを保存しました！")
                st.rerun()

    # --- 入力済みデータ一覧 ---
    st.markdown("<h2>入力済みデータ一覧</h2>", unsafe_allow_html=True)
    sales_data = db.fetch_sales_data(year, month)
    targets_data = db.fetch_targets(year, month)
    targets_df = pd.DataFrame(targets_data)
    sales_df = pd.DataFrame(sales_data)

    if not sales_df.empty:
        sales_df["date"] = pd.to_datetime(sales_df["date"])
        sales_df["日付"] = sales_df["date"].dt.strftime('%Y/%m/%d')
        sales_df["曜日"] = sales_df["date"].dt.dayofweek.map({0:"月",1:"火",2:"水",3:"木",4:"金",5:"土",6:"日"})
        targets_df["date"] = pd.to_datetime(targets_df["date"])
        merged = pd.merge(sales_df, targets_df, on="date", how="left")
        merged["目標売上"] = merged["target_sales"]
        merged["達成率"] = merged.apply(lambda row:
            round(row["actual_sales"] * 100 / row["目標売上"], 2)
            if pd.notnull(row["目標売上"]) and row["目標売上"] > 0 else None, axis=1
        )

        def color_weekday(row):
            d = datetime.strptime(row["日付"], "%Y/%m/%d")
            return f"<span style='color: red'>{row['曜日']}</span>" if utils.is_holiday_or_weekend(d) else row["曜日"]

        merged["曜日"] = merged.apply(color_weekday, axis=1)
        for col in ["目標売上", "actual_sales", "store_sales", "delivery_sales", "other_sales", "unit_price"]:
            merged[col] = merged[col].apply(lambda x: f"{int(x):,}円" if pd.notnull(x) else "")
        merged["客数"] = merged["customer_count"].apply(lambda x: f"{int(x):,}人" if pd.notnull(x) else "")
        merged["達成率"] = merged["達成率"].apply(lambda x: f"<span style='color: blue'>{x:.2f}%</span>" if pd.notnull(x) and x >= 100 else f"<span style='color: red'>{x:.2f}%</span>" if pd.notnull(x) else "")

        merged = merged.rename(columns={
            "actual_sales": "実績",
            "store_sales": "店舗売上",
            "delivery_sales": "デリバリー売上",
            "other_sales": "その他売上",
            "unit_price": "客単価"
        })

        merged["sort_date"] = pd.to_datetime(merged["日付"], format="%Y/%m/%d")
        merged = merged.sort_values("sort_date").drop(columns="sort_date")

        display_cols = ["日付", "曜日", "達成率", "目標売上", "実績", "店舗売上", "デリバリー売上", "その他売上", "客数", "客単価"]

        # --- 合計行 ---
        numeric_cols = ["目標売上", "実績", "店舗売上", "デリバリー売上", "その他売上", "客数", "客単価"]
        cleaned = merged.copy()

        def to_number(x):
            if pd.isnull(x):
                return 0
            return int(str(x).replace("円", "").replace("人", "").replace(",", "").strip())

        total = {col: cleaned[col].apply(to_number).sum() for col in numeric_cols}
        total["客単価"] = round(total["店舗売上"] / total["客数"]) if total["客数"] > 0 else 0
        total["達成率"] = round(total["実績"] * 100 / total["目標売上"], 2) if total["目標売上"] > 0 else ""

        summary_row = {
            "日付": "<b>合計</b>",
            "曜日": "",
            "達成率": f"<span style='color: blue'><b>{total['達成率']:.2f}%</b></span>" if total["達成率"] != "" and total["達成率"] >= 100 else f"<span style='color: red'><b>{total['達成率']:.2f}%</b></span>" if total["達成率"] != "" else "",
            "目標売上": f"<b>{int(total['目標売上']):,}円</b>",
            "実績": f"<b>{int(total['実績']):,}円</b>",
            "店舗売上": f"<b>{int(total['店舗売上']):,}円</b>",
            "デリバリー売上": f"<b>{int(total['デリバリー売上']):,}円</b>",
            "その他売上": f"<b>{int(total['その他売上']):,}円</b>",
            "客数": f"<b>{int(total['客数']):,}人</b>",
            "客単価": f"<b>{int(total['客単価']):,}円</b>"
        }

        merged = pd.concat([merged[display_cols], pd.DataFrame([summary_row])], ignore_index=True)
        styled_html = merged[display_cols].to_html(escape=False, index=False)

        st.markdown(
            f"""
            <div style="overflow-x: auto; overflow-y: auto; height: 300px; border-radius:10px; border: 1px solid #efefef">
                <style>
                    table {{
                        border-collapse: separate;
                        border-spacing: 0;
                    }}
                    th {{
                        position: sticky;
                        top: 0;
                        z-index: 2;
                        white-space: nowrap;
                        text-align :center !important;
                        background-color: #006a38;
                        color: #ffffff;
                    }}
                    td {{
                        white-space: nowrap;
                        text-align: right;
                        height: 50px;
                    }}
                    th:first-child {{
                        left: 0;
                        z-index: 3;
                        background-color: #006a38;
                        color: #ffffff;
                    }}
                    td:first-child {{
                        position: sticky;
                        left: 0;
                        background-color: #f0f2f6;
                        z-index: 1;
                    }}
                </style>
                {styled_html}
            </div>
            """,
            unsafe_allow_html=True
        )

    # --- 更新機能 ---
    st.markdown("<h2>売上データの更新</h2>", unsafe_allow_html=True)
    if not sales_data:
        st.info("更新可能なデータがありません。")
    else:
        date_list = sorted({row["date"] for row in sales_data})
        display_dates = [datetime.strptime(d, "%Y-%m-%d").strftime('%Y/%m/%d') for d in date_list]

        selected = st.selectbox("更新対象の日付", ["選択してください"] + display_dates)
        if selected != "選択してください":
            target_date = datetime.strptime(selected, "%Y/%m/%d").strftime('%Y-%m-%d')
            record = next((r for r in sales_data if r["date"] == target_date), None)

            if record:
                st.write("更新内容を入力してください（未入力は変更しません）")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    new_store = st.number_input("店舗売上", min_value=0, step=1000, value=record["store_sales"])
                with col2:
                    new_delivery = st.number_input("デリバリー売上", min_value=0, step=1000, value=record["delivery_sales"])
                with col3:
                    new_other = st.number_input("その他売上", min_value=0, step=1000, value=record["other_sales"])
                with col4:
                    new_cust = st.number_input("客数", min_value=0, step=1, value=record["customer_count"])

                col_space, col_btn = st.columns([8, 2])
                with col_btn:
                    if st.button("このデータを更新"):
                        new_actual = new_store + new_delivery + new_other
                        new_unit = new_store / new_cust if new_cust else 0

                        db.insert_sales([{
                            "year": record["year"],
                            "month": record["month"],
                            "date": target_date,
                            "store_sales": new_store,
                            "delivery_sales": new_delivery,
                            "other_sales": new_other,
                            "actual_sales": new_actual,
                            "customer_count": new_cust,
                            "unit_price": new_unit
                        }])
                        st.success(f"{selected} の売上データを更新しました")
                        st.rerun()

    # --- 削除処理 ---
    st.markdown("<h2>売上データの削除</h2>", unsafe_allow_html=True)
    if not sales_data:
        st.info("削除可能なデータがありません。")
    else:
        date_list = sorted({row["date"] for row in sales_data})
        display_dates = [datetime.strptime(d, "%Y-%m-%d").strftime('%Y/%m/%d') for d in date_list]

        selected = st.selectbox("削除対象の日付", ["選択してください"] + display_dates, key="delete_select")
        if selected != "選択してください":
            confirm = st.checkbox("⚠️ 本当に削除しますか？", key="delete_confirm")
            if confirm and st.button("このデータを削除"):
                db.delete_sales_by_date(datetime.strptime(selected, "%Y/%m/%d").strftime('%Y-%m-%d'))
                st.success(f"{selected} の売上データを削除しました")
                st.rerun()
