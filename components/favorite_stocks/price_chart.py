import streamlit as st
import pandas as pd
import altair as alt

from services.favorite_stocks.stock_data import get_stock_data

def render_price_chart(favorites, selected_group):
    st.subheader("최근 가격 변동 (정규화)")
    group_tickers = favorites.get(selected_group, [])
    if not group_tickers:
        st.info("티커가 없으므로 차트를 표시할 수 없습니다.")
        return

    period_options = {"1개월": 30, "3개월": 90, "6개월": 180, "1년": 365}
    selected_period_label = st.radio(
        "기간 선택", options=list(period_options.keys()), index=1
    )
    period_days = period_options[selected_period_label]

    selected_tickers = st.multiselect(
        "종목 선택", options=group_tickers, default=group_tickers
    )
    if not selected_tickers:
        st.info("표시할 종목이 없습니다.")
        return

    chart_df = pd.DataFrame()
    for ticker in selected_tickers:
        df = get_stock_data(ticker)
        if df is None or df.empty or len(df) < period_days:
            continue
        df_recent = df.tail(period_days)["Close"]
        norm_price = df_recent - df_recent.iloc[0]
        norm_price = norm_price.reset_index()
        norm_price["ticker"] = ticker
        chart_df = pd.concat([chart_df, norm_price], ignore_index=True)

    if chart_df.empty:
        st.info("선택한 기간에 대해 충분한 데이터가 없습니다.")
        return

    selection = alt.selection_multi(fields=['ticker'], bind='legend')
    chart = alt.Chart(chart_df).mark_line().encode(
        x=alt.X("Date:T", title="날짜"),
        y=alt.Y("Close:Q", title="정규화 변동"),
        color=alt.Color("ticker:N", title="티커"),
        tooltip=["Date:T", "ticker:N", "Close:Q"]
    ).add_selection(
        selection
    ).properties(
        height=650
    )
    st.altair_chart(chart.interactive(), use_container_width=True)
