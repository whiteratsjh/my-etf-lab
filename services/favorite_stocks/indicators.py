import os
import pandas as pd
import numpy as np
import logging

from utils.constants import STOCK_INSIGHT_DIR, TODAY_STR, FILE_EXPIRY_DAYS
from services.favorite_stocks.stock_data import cleanup_old_files

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s:%(message)s")

def calculate_indicators(df):
    indicators = {}

    df["MA20"] = df["Close"].rolling(window=20).mean()
    df["MA125"] = df["Close"].rolling(window=125).mean()
    df["MA200"] = df["Close"].rolling(window=200).mean()
    
    start_price = df["Close"].iloc[0]
    end_price = df["Close"].iloc[-1]
    indicators["전체변동률평균"] = (end_price / start_price - 1) * 100

    df["Return"] = df["Close"].pct_change()
    std_return = df["Return"].std() * 100
    indicators["표준편차"] = std_return
    indicators["-1 시그마"] = -1 * std_return
    indicators["-2 시그마"] = -2 * std_return
    indicators["-3 시그마"] = -3 * std_return

    delta = df["Close"].diff()
    gain = delta.clip(lower=0).rolling(window=14).mean()
    loss = -delta.clip(upper=0).rolling(window=14).mean()
    RS = gain / loss
    RSI = 100 - (100 / (1 + RS))
    indicators["RSI"] = RSI.iloc[-1] if not RSI.empty else np.nan

    low_min = df["Low"].rolling(window=14).min()
    high_max = df["High"].rolling(window=14).max()
    stoch = 100 * ((df["Close"] - low_min) / (high_max - low_min))
    indicators["Stoch"] = stoch.iloc[-1] if not stoch.empty else np.nan

    indicators["RSI-Stoch"] = (
        (indicators["RSI"] + indicators["Stoch"]) / 2
        if not np.isnan(indicators["RSI"]) and not np.isnan(indicators["Stoch"])
        else np.nan
    )

    indicators["MA20"] = df["MA20"].iloc[-1]
    indicators["MA125"] = df["MA125"].iloc[-1]
    indicators["MA200"] = df["MA200"].iloc[-1]

    current_price = df["Close"].iloc[-1]
    indicators["단기이격도"] = (current_price - indicators["MA20"]) / indicators["MA20"] * 100
    indicators["중기이격도"] = (current_price - indicators["MA125"]) / indicators["MA125"] * 100
    indicators["장기이격도"] = (current_price - indicators["MA200"]) / indicators["MA200"] * 100

    return indicators

def interpret_gap_signal(gap, label):
    gap_r = round(gap, 1)
    if gap >= 2:
        signal = "매수"
        color = "red"
    elif gap <= -2:
        signal = "매도"
        color = "blue"
    else:
        signal = "중립"
        color = "gray"
    return f"{label}: <span style='color:{color};'>{signal}</span> ({gap_r:+.1f}%)"

def interpret_aux_signal(value, label):
    val_r = round(value, 1)
    if value < 30:
        signal = "매수"
        color = "red"
    elif value > 70:
        signal = "매도"
        color = "blue"
    else:
        signal = "중립"
        color = "gray"
    return f"{label}: <span style='color:{color};'>{signal}</span> ({val_r:.1f})"

def save_stock_insight(ticker, indicators):
    cleanup_old_files(STOCK_INSIGHT_DIR)
    file_path = os.path.join(STOCK_INSIGHT_DIR, f"{ticker}_{TODAY_STR}.csv")
    df_insight = pd.DataFrame([indicators])
    df_insight.to_csv(file_path, index=False)
    logging.info(f"Saved stock insight for {ticker} to {file_path}")
