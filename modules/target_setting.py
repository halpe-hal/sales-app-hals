# modules/target_setting.py（新店舗版：カテゴリなし）

import streamlit as st
import pandas as pd
import calendar
from datetime import datetime, date
import jpholiday
from modules import utils
from modules import supabase_db as db


def show():
    st.markdown("<h2>売上目標の設定</h2>", unsafe_allow_html=True)

    # --- 管理者チェック ---
    if "user" not in st.session_state or st.session_state["user"]["email"] not in ["nishimura@kklia.com"]:
        st.warning("この画面にはアクセスできません。")
        st.stop()

    current_year = datetime.now().year
    year = st.selectbox(
        "年を選択",
        list(range(2024, 2101)),
        index=list(range(2024, 2101)).index(current_year),
        key="target_year"
    )

    # --- 月タブ切り替え ---
    month_tabs = st.tabs([f"{m}月" for m in range(1, 13)])

    for j, month in enumerate(range(1, 13)):
        with month_tabs[j]:
            key_prefix = f"{year}_{month}"

            # --- 月間一括登録 ---
            st.subheader("月間一括登録（平日・休日）")
            col1, col2 = st.columns(2)
            with col1:
                weekday_target = st.number_input("平日の目標売上 (円)", 0, 2000000, step=1000, key=f"{key_prefix}_weekday")
            with col2:
                holiday_target = st.number_input("土日祝の目標売上 (円)", 0, 2000000, step=1000, key=f"{key_prefix}_holiday")

            col_space, col_btn = st.columns([8, 2])
            with col_btn:
                if st.button("一括登録（上書きあり）", key=f"{key_prefix}_bulk_btn"):
                    for day in range(1, calendar.monthrange(year, month)[1] + 1):
                        dt = date(year, month, day)
                        value = holiday_target if utils.is_holiday_or_weekend(dt) else weekday_target
                        db.upsert_target(year, month, dt.strftime("%Y-%m-%d"), value)
                    st.success("一括登録が完了しました！")
                    st.rerun()

            # --- 個別日設定 ---
            st.subheader("個別日設定")
            col3, col4 = st.columns(2)
            with col3:
                selected_date = st.date_input("対象日を選択", date(year, month, 1), key=f"{key_prefix}_date")
            with col4:
                individual_target = st.number_input("個別日の目標売上 (円)", 0, 2000000, step=1000, key=f"{key_prefix}_individual")

            col_space2, col_btn2 = st.columns([8, 2])
            with col_btn2:
                if st.button("個別日を保存", key=f"{key_prefix}_save_btn"):
                    db.upsert_target(
                        selected_date.year,
                        selected_date.month,
                        selected_date.strftime("%Y-%m-%d"),
                        individual_target
                    )
                    st.success("個別日の目標を保存しました！")
                    st.rerun()

            # --- カレンダー表示 ---
            targets_data = db.fetch_targets(year, month)
            df = pd.DataFrame(targets_data)

            if df.empty:
                st.info("この月のデータは未設定です。")
                continue

            df["date"] = pd.to_datetime(df["date"])
            target_map = {d.date(): v for d, v in zip(df["date"], df["target_sales"])}

            cal = calendar.Calendar(firstweekday=6)
            weeks = cal.monthdatescalendar(year, month)

            table = "<table style='border-collapse: collapse; width: 100%; text-align: center;'>"
            table += "<tr>" + "".join([f"<th>{d}</th>" for d in ["日", "月", "火", "水", "木", "金", "土"]]) + "</tr>"

            for week in weeks:
                table += "<tr>"
                for day in week:
                    if day.month != month:
                        table += "<td style='background-color: #f0f0f0;'>-</td>"
                    else:
                        value = f"\u00a5{int(target_map.get(day, 0)):,}" if day in target_map else "未設定"
                        color = "red" if utils.is_holiday_or_weekend(day) else "black"
                        table += f"<td style='padding: 4px; border: 1px solid #ddd; color: {color};'>{day.day}<br><small>{value}</small></td>"
                table += "</tr>"

            table += "</table>"
            st.markdown(table, unsafe_allow_html=True)

            # --- 月間合計 ---
            st.subheader(f"月間合計目標売上: \u00a5{int(sum(target_map.values())):,}")
