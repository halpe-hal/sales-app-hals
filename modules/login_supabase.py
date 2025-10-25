# modules/login_supabase.py

import streamlit as st
from modules.supabase_client import supabase
from streamlit_javascript import st_javascript

def check_login():
    refresh_token = st_javascript("window.localStorage.getItem('refresh_token');", key="get_refresh")

    # JS評価がまだなら中断
    if refresh_token is None and "user" not in st.session_state:
        st.info("ログイン状態を確認中です…")
        st.stop()

    # refresh_token があるなら再ログイン
    if refresh_token and "access_token" not in st.session_state:
        try:
            res = supabase.auth.refresh_session(refresh_token)
            if res.session:
                st.session_state["user"] = {
                    "id": res.user.id,
                    "email": res.user.email
                }
                st.session_state["access_token"] = res.session.access_token
                # localStorage も更新
                st_javascript(f"""
                    window.localStorage.setItem('refresh_token', '{res.session.refresh_token}');
                """)
        except Exception as e:
            st.session_state.pop("access_token", None)
            st.session_state.pop("user", None)

    # ログインフォーム
    if "user" not in st.session_state:
        with st.form("login_form"):
            st.subheader("ログイン")
            email = st.text_input("メールアドレス")
            password = st.text_input("パスワード", type="password")
            submitted = st.form_submit_button("ログイン")

            if submitted:
                try:
                    res = supabase.auth.sign_in_with_password({
                        "email": email,
                        "password": password
                    })
                    if res.session:
                        st.session_state["user"] = {
                            "id": res.user.id,
                            "email": res.user.email
                        }
                        st.session_state["access_token"] = res.session.access_token

                        # refresh_token を保存
                        st_javascript(f"""
                            window.localStorage.setItem('refresh_token', '{res.session.refresh_token}');
                        """)
                        st.success("ログイン成功")
                        st.rerun()
                    else:
                        st.error("ログインに失敗しました。")
                except Exception as e:
                    st.error("メールアドレスまたはパスワードが間違っています。")
        st.stop()

def logout():
    # localStorageのrefresh_tokenを削除
    st_javascript("window.localStorage.removeItem('refresh_token');", key="remove_refresh")
    st.session_state.clear()
    st.success("ログアウトしました")
    st.rerun()
