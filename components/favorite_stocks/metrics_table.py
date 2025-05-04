import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf

from services.favorite_stocks.stock_data import get_stock_data
from services.favorite_stocks.indicators import (
    calculate_indicators,
    save_stock_insight
)

def get_gap_signal_text(gap, label):
    gap_r = round(gap, 1)
    if label == "단기":
        threshold = 5
    elif label == "중기":
        threshold = 10
    elif label == "장기":
        threshold = 15
    else:
        threshold = 10
    if gap >= threshold:
        signal = "매도"
    elif gap <= -threshold:
        signal = "매수"
    else:
        signal = "중립"
    return f"{label}: {signal} ({gap_r:+.1f}%)"

def get_aux_signal_text(value, label):
    val_r = round(value, 1)
    if value < 30:
        signal = "매수"
    elif value > 70:
        signal = "매도"
    else:
        signal = "중립"
    return f"{label}: {signal} ({val_r:.1f})"

def color_aux(val):
    try:
        fval = float(val)
    except:
        return ""
    if fval <= 30:
        return "color: blue"
    elif fval >= 70:
        return "color: red"
    else:
        return ""

def render_metrics_table(favorites, selected_group):
    st.subheader("주요 지표 테이블")
    group_tickers = favorites.get(selected_group, [])
    if not group_tickers:
        st.info("추가된 티커가 없습니다.")
        return

    metrics_list = []
    for ticker in group_tickers:
        df = get_stock_data(ticker)
        if df is None or df.empty:
            continue
        indicators = calculate_indicators(df)
        save_stock_insight(ticker, indicators)
        try:
            tkr_obj = yf.Ticker(ticker)
            info = tkr_obj.info
            name = info.get("shortName", "N/A")
            current_price = info.get("regularMarketPrice", df["Close"].iloc[-1])
        except Exception:
            name = "N/A"
            current_price = df["Close"].iloc[-1]

        entry = {
            "티커": ticker,
            "종목명": name,
            "현재가": current_price,
            "변동률(%)": round(indicators.get("전체변동률평균", np.nan), 2),
            "표준편차(%)": round(indicators.get("표준편차", np.nan), 2),
            "-1 시그마": round(indicators.get("-1 시그마", np.nan), 2),
            "-2 시그마": round(indicators.get("-2 시그마", np.nan), 2),
            "-3 시그마": round(indicators.get("-3 시그마", np.nan), 2),
            "RSI": round(indicators.get("RSI", np.nan), 2),
            "Stoch": round(indicators.get("Stoch", np.nan), 2),
            "RSI-Stoch": round(indicators.get("RSI-Stoch", np.nan), 2),
            "MA20": round(indicators.get("MA20", np.nan), 2),
            "MA125": round(indicators.get("MA125", np.nan), 2),
            "MA200": round(indicators.get("MA200", np.nan), 2)
        }

        gap_short = get_gap_signal_text(indicators.get("단기이격도", 0), "단기")
        gap_mid   = get_gap_signal_text(indicators.get("중기이격도", 0), "중기")
        gap_long  = get_gap_signal_text(indicators.get("장기이격도", 0), "장기")
        entry["📈 이격도 신호"] = f"{gap_short} / {gap_mid} / {gap_long}"
        
        aux_rsi = get_aux_signal_text(indicators.get("RSI", np.nan), "RSI")
        aux_stoch = get_aux_signal_text(indicators.get("Stoch", np.nan), "Stoch")
        aux_rsistoch = get_aux_signal_text(indicators.get("RSI-Stoch", np.nan), "RSI-Stoch")
        entry["🧭 보조지표 신호"] = f"{aux_rsi} / {aux_stoch} / {aux_rsistoch}"

        metrics_list.append(entry)
    
    if metrics_list:
        df_metrics = pd.DataFrame(metrics_list)
        df_metrics = df_metrics[[ 
            "티커", "종목명", "현재가", "변동률(%)", "표준편차(%)",
            "-1 시그마", "-2 시그마", "-3 시그마",
            "RSI", "Stoch", "RSI-Stoch",
            "MA20", "MA125", "MA200",
            "📈 이격도 신호", "🧭 보조지표 신호"
        ]]
        styled = (df_metrics.style
                  .applymap(color_aux, subset=["RSI", "Stoch", "RSI-Stoch"])
                  .hide(axis="index"))
        st.dataframe(styled, use_container_width=True)
    else:
        st.info("지표를 계산할 수 있는 데이터가 없습니다.")
