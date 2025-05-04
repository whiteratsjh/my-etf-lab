import streamlit as st
import numpy as np
import yfinance as yf
import pandas as pd

from services.favorite_stocks.stock_data import get_stock_data
from services.favorite_stocks.indicators import calculate_indicators
from components.favorite_stocks.metrics_table import get_gap_signal_text

def get_aux_signal_insight(value, label):
    val_r = round(value, 1)
    if value < 30:
        signal = "과매도"
    elif value > 70:
        signal = "과열"
    else:
        signal = "중립"
    return f"{label}: {signal} ({val_r:.1f})"

def get_bollinger_insight(df):
    try:
        ma20 = df["Close"].rolling(window=20).mean().iloc[-1]
        std20 = df["Close"].rolling(window=20).std().iloc[-1]
        upper = ma20 + 2 * std20
        lower = ma20 - 2 * std20
        close = df["Close"].iloc[-1]

        rel_diff = (close - ma20) / ma20 * 100
        if abs(rel_diff) <= 1:
            center_pos = "중심선 부근"
        elif rel_diff > 1:
            center_pos = "중심선 위"
        else:
            center_pos = "중심선 아래"

        band_width = (upper - lower) / ma20 * 100
        if band_width <= 5:
            band_desc = "밴드 폭 매우 좁음"
        elif band_width <= 10:
            band_desc = "밴드 폭 적당"
        else:
            band_desc = "밴드 폭 넓음"

        if len(df) >= 25:
            ma20_prev = df["Close"].rolling(window=20).mean().iloc[-6]
            std20_prev = df["Close"].rolling(window=20).std().iloc[-6]
            upper_prev = ma20_prev + 2 * std20_prev
            lower_prev = ma20_prev - 2 * std20_prev
            band_width_prev = (upper_prev - lower_prev) / ma20_prev * 100
            if band_width > band_width_prev:
                trend = "밴드 폭 확장 중"
            elif band_width < band_width_prev:
                trend = "밴드 폭 축소 중"
            else:
                trend = "밴드 폭 변화 없음"
        else:
            trend = "추세 분석 불가"

        if center_pos == "중심선 위" and band_desc == "밴드 폭 넓음" and trend == "밴드 폭 확장 중":
            possibility = "상승추세 강화 가능성"
        elif center_pos == "중심선 아래" and band_desc == "밴드 폭 매우 좁음" and trend == "밴드 폭 축소 중":
            possibility = "하락 or 횡보 가능성"
        elif center_pos == "중심선 부근" and band_desc == "밴드 폭 매우 좁음" and trend == "밴드 폭 축소 중":
            possibility = "대규모 변동성 예고"
        else:
            possibility = "추세 불확실"

        return f"[볼린저밴드] {center_pos} / {band_desc} / {trend} → {possibility}"
    except Exception:
        return "볼린저밴드 계산 불가"

def render_insights_text(favorites, selected_group):
    st.subheader("종목별 인사이트 요약")
    group_tickers = favorites.get(selected_group, [])
    if not group_tickers:
        st.info("인사이트를 출력할 종목이 없습니다.")
        return

    insights = []
    for ticker in sorted(group_tickers):
        df = get_stock_data(ticker)
        if df is None or df.empty:
            continue
        indicators = calculate_indicators(df)
        try:
            tkr_obj = yf.Ticker(ticker)
            info = tkr_obj.info
            name = info.get("shortName", "N/A")
            current_price = info.get("regularMarketPrice", df["Close"].iloc[-1])
        except Exception:
            name = "N/A"
            current_price = df["Close"].iloc[-1]

        summary = f"티커: {ticker}  현재가: {round(current_price,2)} USD  전체 변동률: {round(indicators.get('전체변동률평균',np.nan),1):+.1f}%\n"

        gap_short = get_gap_signal_text(indicators.get("단기이격도", 0), "단기")
        gap_mid   = get_gap_signal_text(indicators.get("중기이격도", 0), "중기")
        gap_long  = get_gap_signal_text(indicators.get("장기이격도", 0), "장기")
        summary += f"[이격도 신호] {gap_short}  {gap_mid}  {gap_long}\n"

        aux_rsi = get_aux_signal_insight(indicators.get("RSI", np.nan), "RSI")
        aux_stoch = get_aux_signal_insight(indicators.get("Stoch", np.nan), "Stoch")
        aux_rsistoch = get_aux_signal_insight(indicators.get("RSI-Stoch", np.nan), "RSI-Stoch")
        summary += f"[보조지표 신호] {aux_rsi}  {aux_stoch}  {aux_rsistoch}\n"

        bollinger = get_bollinger_insight(df)
        summary += f"[볼린저밴드] {bollinger}\n"

        insights.append(summary)

    if insights:
        full_text = "\n".join(insights)
        st.code(full_text, language="text")
        st.download_button("인사이트 텍스트 복사", full_text, file_name="insights.txt", mime="text/plain")
    else:
        st.info("종목별 인사이트를 생성할 데이터가 없습니다.")
