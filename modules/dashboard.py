# modules/dashboard.py（新店舗版・客単価修正版）

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from modules import supabase_db as db
from modules import utils

def show():
    st.markdown("<h2>ダッシュボード</h2>", unsafe_allow_html=True)
    show_dashboard_tab("HAL'S BAGEL. 自由が丘店")

def show_dashboard_tab(name):
    st.markdown(f"<h3>{name} の年間目標達成率</h3>", unsafe_allow_html=True)

    today = datetime.today()
    sales_data = db.fetch_sales_data(year=today.year)
    sales_df = pd.DataFrame(sales_data)

    if sales_df.empty:
        st.info("⚠️ 売上データが存在しません。")
        return

    sales_df["date"] = pd.to_datetime(sales_df["date"])
    sales_df = sales_df.sort_values("date")

    # --- 実績合計と目標合計の計算 ---
    last_date = sales_df["date"].max().strftime("%Y-%m-%d")
    start_of_year = datetime(today.year, 1, 1).strftime("%Y-%m-%d")

    actual_total = sales_df[
        (sales_df["date"] >= start_of_year) & (sales_df["date"] <= last_date)
    ]["actual_sales"].sum()

    targets = db.fetch_targets(year=today.year)
    targets_df = pd.DataFrame(targets)
    if not targets_df.empty:
        targets_df["date"] = pd.to_datetime(targets_df["date"])
        targets_total = targets_df[
            (targets_df["date"] >= start_of_year) & (targets_df["date"] <= last_date)
        ]["target_sales"].sum()
    else:
        targets_total = 0

    if targets_total > 0:
        achievement = round(actual_total * 100 / targets_total, 2)
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("達成率", f"{achievement:.2f}%")
        with col2:
            st.metric("年間目標", f"¥{int(targets_total):,}")
        with col3:
            st.metric("実績合計", f"¥{int(actual_total):,}")
    else:
        st.info("⚠️ 目標が設定されていません。")

    # --- グラフ期間切り替え ---
    timeframe_tabs = {
        "今月": (datetime(today.year, today.month, 1), today),
        "先月": (
            datetime(today.year, today.month - 1, 1) if today.month > 1 else datetime(today.year - 1, 12, 1),
            datetime(today.year, today.month, 1) - timedelta(days=1)
        ),
        "直近3ヶ月": (today - timedelta(days=90), today),
        "直近1年": (today - timedelta(days=365), today),
        "全体": (datetime(2024, 1, 1), today),
        "任意期間": None
    }

    tf_tab_names = list(timeframe_tabs.keys())
    tf_tab_objs = st.tabs(tf_tab_names)

    for i, tf_tab in enumerate(tf_tab_objs):
        with tf_tab:
            label = tf_tab_names[i]

            # --- 日付選択 ---
            if label == "任意期間":
                col1, col2 = st.columns(2)
                start_date = col1.date_input("開始日", value=today - timedelta(days=30), key=f"start_{label}")
                end_date = col2.date_input("終了日", value=today, key=f"end_{label}")
                start_date = datetime.combine(start_date, datetime.min.time())
                end_date = datetime.combine(end_date, datetime.max.time())
            else:
                start_date, end_date = timeframe_tabs[label]

            # --- データ抽出 ---
            df = sales_df.copy()
            df["customer_count"] = df["customer_count"].apply(utils.safe_convert_to_int)
            df = df[(df["date"] >= start_date) & (df["date"] <= end_date)]

            if df.empty:
                st.info("該当するデータがありません。")
                continue

            # --- 集計処理 ---
            summary = df.groupby("date").agg({
                "store_sales": "sum",        # ← 店舗売上を追加
                "actual_sales": "sum",
                "customer_count": "sum"
            }).reset_index()

            # ✅ 修正点：客単価 = 店舗売上 ÷ 客数（正）
            summary["unit_price"] = summary.apply(
                lambda r: r["store_sales"] / r["customer_count"] if r["customer_count"] else 0,
                axis=1
            )

            summary["date"] = summary["date"].dt.strftime("%Y/%m/%d")

            # --- y軸スケール（目安） ---
            limits = {"売上": None, "客数": None, "客単価": None}

            # --- 売上グラフ ---
            fig_sales = px.line(summary, x="date", y="actual_sales", title="売上推移", labels={"actual_sales": "売上（円）"})
            fig_sales.update_traces(mode="lines+markers")
            fig_sales.update_layout(yaxis=dict(range=[0, limits["売上"]]), xaxis_title="日付")
            fig_sales.update_yaxes(tickformat=",")
            st.plotly_chart(fig_sales, use_container_width=True, key=f"sales_chart_{label}")

            # --- 客数グラフ ---
            fig_customers = px.line(summary, x="date", y="customer_count", title="客数推移", labels={"customer_count": "客数（人）"})
            fig_customers.update_traces(mode="lines+markers")
            fig_customers.update_layout(yaxis=dict(range=[0, limits["客数"]]), xaxis_title="日付")
            st.plotly_chart(fig_customers, use_container_width=True, key=f"customers_chart_{label}")

            # --- 客単価グラフ（修正版） ---
            fig_unit = px.line(summary, x="date", y="unit_price", title="客単価推移", labels={"unit_price": "客単価（円）"})
            fig_unit.update_traces(mode="lines+markers")
            fig_unit.update_layout(yaxis=dict(range=[0, limits["客単価"]]), xaxis_title="日付")
            fig_unit.update_yaxes(tickformat=",")
            st.plotly_chart(fig_unit, use_container_width=True, key=f"unit_price_chart_{label}")
