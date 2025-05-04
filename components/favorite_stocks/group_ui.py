import streamlit as st
from services.favorite_stocks.favorites_io import save_favorites

def render_group_management(favorites):
    with st.expander("관심그룹 관리", expanded=False):
        with st.form(key="group_management_form"):
            new_group = st.text_input("새로운 관심그룹 이름")
            col1, col2 = st.columns(2)
            with col1:
                add_btn = st.form_submit_button("추가")
            with col2:
                del_group = st.selectbox("삭제할 관심그룹 선택", options=[""] + list(favorites.keys()))
                del_btn = st.form_submit_button("삭제")
        if add_btn and new_group:
            if new_group in favorites:
                st.warning("이미 존재하는 그룹입니다.")
            else:
                favorites[new_group] = []
                save_favorites(favorites)
                st.success(f"관심그룹 '{new_group}' 추가됨.")
                st.rerun()
        if del_btn and del_group:
            if del_group in favorites:
                favorites.pop(del_group)
                save_favorites(favorites)
                st.success(f"관심그룹 '{del_group}' 삭제됨.")
                st.rerun()

def render_ticker_addition(favorites, selected_group):
    with st.expander(f"그룹 [{selected_group}] 종목 관리", expanded=False):
        group_tickers = favorites.get(selected_group, [])
        with st.form(key="ticker_add_form"):
            new_ticker = st.text_input("추가할 티커 (예: AAPL)")
            add_ticker_btn = st.form_submit_button("티커 추가")
        if add_ticker_btn and new_ticker:
            new_ticker = new_ticker.upper().strip()
            if new_ticker in group_tickers:
                st.warning("이미 등록된 티커입니다.")
            elif len(group_tickers) >= 20:
                st.warning("최대 20개 티커까지 등록할 수 있습니다.")
            else:
                group_tickers.append(new_ticker)
                favorites[selected_group] = group_tickers
                save_favorites(favorites)
                st.success(f"{new_ticker} 티커가 그룹에 추가되었습니다.")
                st.rerun()
        st.write("현재 등록된 티커:", group_tickers)
