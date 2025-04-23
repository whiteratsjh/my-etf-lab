import streamlit as st
import yfinance as yf
import math


def fetch_usdkrw_rate():
    try:
        krw_data = yf.Ticker("KRW=X").history(period="1d")
        return krw_data['Close'].iloc[-1] if not krw_data.empty else None
    except:
        return None

def fetch_stock_price(ticker):
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1d")
        return hist['Close'].iloc[-1] if not hist.empty else None
    except:
        return None

def render():
    st.header("📊 매수 계산기")

    mode = st.radio("계산 모드 선택", ["필요한 원화 환전 금액 계산", "보유 달러로 최대 몇 주 매수 가능?", "물타기 후 새로운 평단가 계산"], index=0)

    if mode == "필요한 원화 환전 금액 계산":
        col1, col2 = st.columns(2)
        with col1:
            ticker = st.text_input("티커 입력 (예: SCHD)", "SCHD")
        with col2:
            shares = st.number_input("매수할 주식 수", min_value=1, step=1, value=10)

        price = fetch_stock_price(ticker)
        rate = fetch_usdkrw_rate()

        if price and rate:
            rounded_rate = math.ceil(rate / 10) * 10
            st.markdown(f"현재가: ${price:.2f} (Yahoo Finance 기준)")
            st.markdown(f"환율: {rate:.2f} → 계산 시 적용 환율: {rounded_rate}원")

            total_usd = price * shares
            total_krw = total_usd * rounded_rate

            st.markdown("""
            ### 🪙 예상 환전 금액
            - **필요한 달러 금액:** ${:.2f}  
            - **필요한 원화 입금액:** {:,.0f}원
            """.format(total_usd, total_krw))

    elif mode == "보유 달러로 최대 몇 주 매수 가능?":
        ticker = st.text_input("티커 입력 (예: SCHD)", "SCHD")
        dollar_amount = st.number_input("보유 달러 금액 ($)", min_value=0.0, value=100.0, step=10.0)
        price = fetch_stock_price(ticker)
        if price:
            max_shares = math.floor(dollar_amount / price)
            leftover = dollar_amount - (price * max_shares)
            st.markdown(f"✅ **{max_shares}주** 매수 가능, 잔여 금액: ${leftover:.2f}")

    elif mode == "물타기 후 새로운 평단가 계산":
        cur_avg_price = st.number_input("현재 평단가 ($)", min_value=0.0, value=27.50, step=0.01)
        cur_qty = st.number_input("현재 보유 수량 (주)", min_value=1, value=45, step=1)
        add_qty = st.number_input("추가 매수 수량 (주)", min_value=1, value=10, step=1)

        ticker = st.text_input("티커 입력 (예: SCHD)", "SCHD")
        price = fetch_stock_price(ticker)

        if price:
            total_cost = cur_avg_price * cur_qty + price * add_qty
            total_qty = cur_qty + add_qty
            new_avg = total_cost / total_qty
            st.markdown(f"🔄 매수 후 새로운 평단가: **${new_avg:.2f}**")