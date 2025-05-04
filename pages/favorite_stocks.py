import os, sys
import streamlit as st
from services.favorite_stocks.favorites_io import load_favorites
from components.favorite_stocks.group_ui import render_group_management, render_ticker_addition
from components.favorite_stocks.metrics_table import render_metrics_table
from components.favorite_stocks.price_chart import render_price_chart
from components.favorite_stocks.insights_text import render_insights_text

def render():
    st.title("관심 종목 관리")
    favorites = load_favorites()
    
    st.sidebar.subheader("Favorite Groups")
    st.sidebar.write(favorites)
    
    # Check if there are any favorite groups available:
    if not favorites or not isinstance(favorites, dict) or len(favorites) == 0:
        st.info("먼저 관심 그룹을 추가해주세요.")
        return
    
    # 1. 그룹 선택: 선택 상자에 favorites의 키들을 출력
    selected_group = st.selectbox("관심 그룹 선택", list(favorites.keys()))
    
    # If, for some reason, no group is selected, display an info message and stop.
    if not selected_group:
        st.info("먼저 관심 그룹을 추가해주세요.")
        return
    
    # 3. If a group is selected, render the rest of the UI in order.
    # a. 지표 테이블
    render_metrics_table(favorites, selected_group)
    # b. 가격 차트
    render_price_chart(favorites, selected_group)
    # c. 인사이트 요약
    render_insights_text(favorites, selected_group)
    # d. 그룹 관리 UI
    render_group_management(favorites)
    # e. 종목 추가/삭제 UI
    render_ticker_addition(favorites, selected_group)

# Expose render() to be used in streamlit_app.py
