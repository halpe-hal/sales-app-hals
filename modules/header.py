# modules/header.py

import streamlit as st

def show():
    st.markdown(
        """
        <style>
        .custom-header {
            background-color: #006a38;
            color: #ffffff;
            padding: 12px 24px;
            font-size: 20px;
            font-weight: bold;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            z-index: 999999;
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
        }

        .main > div:first-child {
            padding-top: 70px !important;
        }

        /* メイン画面の最大幅を強制的に広げる */
        section.stMain > div { 
            max-width: 1000px !important;
            padding-top: 60px;
        }

        /* サイドバーの幅を調整 */
        section[data-testid="stSidebar"] {
            width: 220px !important;     /* サイドバー全体の幅 */
            min-width: 220px !important;
            max-width: 220px !important;
        }
        /* サイドバー内のコンテンツの余白も調整（必要なら） */
        .css-1d391kg.e1fqkh3o5 {  
            padding-left: 10px;
            padding-right: 10px;
        }

        .st-emotion-cache-kgpedg {
            padding-bottom: 0;
        }

        .st-emotion-cache-1f3w014 {
            margin-top: 35px;
        }

        h2 {
            position: relative;
            font-size: 24px !important;
            font-weight: bold;
            padding: 2% !important;
            margin-bottom: 3% !important;
            }

        h2::before {
            position: absolute;
            content: '';
            left: 0;
            bottom: 0;
            width: 100px;
            height: 5px;
            background: #006a38;
            z-index: 1;
        }
        
        h2::after {
            position: absolute;
            content: '';
            left: 0;
            bottom: 0;
            width: 100%;
            height: 5px;
            background: #efefef;
        }

        h3 {
            border-bottom: 1px solid #006a38;
            padding: 0 0 1% 1% !important;
            font-size: 20px !important;
            margin-bottom: 1% !important;
        }

        h4 {
            margin-top: 20px !important;
        }
        </style>
        <div class="custom-header">
            HAL'S BAGEL. 自由が丘店 売上管理
        </div>
        """,
        unsafe_allow_html=True
    )
