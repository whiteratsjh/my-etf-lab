import streamlit as st
from urllib.parse import unquote
from components.nav import render_nav
import importlib

# app.py 제일 앞에
import os, time
print("🔄 앱 실행됨:", time.ctime(), "경로:", os.getcwd())

import os
import time
print("📍 앱 시작됨:", time.ctime())
print("📂 현재 디렉토리:", os.getcwd())
print("📁 현재 폴더 내용:", os.listdir("."))


# 마지막에 설정해야 하는 set_page_config 호출
st.set_page_config(page_title="Market App", layout="wide", initial_sidebar_state="collapsed")

# 기본 사이드바 및 토글 아이콘 숨기기
st.markdown(
    """
    <style>
        [data-testid="stSidebar"],
        [data-testid="stSidebarNav"],
        [data-testid="collapsedControl"] {
            display: none;
        }
    </style>
    """,
    unsafe_allow_html=True
)
st.markdown(
    """
    <style>
        [data-testid="stSidebarCollapsedControl"] {
            display: none !important;
        }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown("""
    <style>
        .block-container {
            padding-top: 1rem !important;
        }
    </style>
""", unsafe_allow_html=True)

# 코드뷰기를 위해 초기 페이지 값 결정
query_params = st.experimental_get_query_params()
current_page = query_params.get("page", "dashboard")
current_page = unquote(current_page)

# 상단 대신 수직 네비게이션 바 렌더링
with st.container():
    render_nav(current_page, direction="vertical")
    print("✅ render_nav 렌더링 성공")


# 페이지 렌더링 번기 (최신 모듈 리로드 포함)
if current_page == "dashboard":
    import pages.dashboard as dashboard
    importlib.reload(dashboard)
    print(f"📄 {current_page}.render() 호출 시도")
    dashboard.render()
elif current_page == "dividends":
    import pages.dividends as dividends
    importlib.reload(dividends)
    print(f"📄 {current_page}.render() 호출 시도")
    dividends.render()
elif current_page == "etfs":  
    import pages.etfs as etfs
    importlib.reload(etfs)
    print(f"📄 {current_page}.render() 호출 시도")
    etfs.render()
elif current_page == "stocks": 
    import pages.stocks as stocks
    importlib.reload(stocks)
    print(f"📄 {current_page}.render() 호출 시도")
    stocks.render()
elif current_page == "stock_calc":
    import pages.stock_calc as stock_calc
    importlib.reload(stock_calc)
    print(f"📄 {current_page}.render() 호출 시도")
    stock_calc.render()
else:
    st.error("Page not found.")

print("🧭 current_page =", current_page)
