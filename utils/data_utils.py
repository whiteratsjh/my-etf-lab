import streamlit as st
import requests
import pandas as pd
import yfinance as yf
from bs4 import BeautifulSoup

# 금리 및 지수 가격 조회
def fetch_price(ticker: str):
    try:
        data = yf.Ticker(ticker).history(period="1d")
        if not data.empty:
            return data['Close'].iloc[-1]
        else:
            return None
    except Exception:
        return None

# 배당 정보 크롤링
@st.cache_data(ttl=3600)
def get_etf_dividend_data(ticker: str) -> pd.DataFrame:
    print(f"[{ticker.upper()}] 🧰 웹에서 수집 (캐시 무상 또는 TTL 만료 시)")

    url = f"https://stockanalysis.com/etf/{ticker.upper()}/dividend/"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch page: {response.status_code}")

    soup = BeautifulSoup(response.text, "html.parser")
    div_table = soup.find("div", attrs={"data-test": "dividend-table"})
    if div_table is None:
        raise Exception("Cannot find dividend table div")

    table = div_table.find("table")
    if table is None:
        raise Exception("Cannot find table tag")

    tbody = table.find("tbody")
    if tbody is None:
        raise Exception("Cannot find tbody")

    rows = []
    for tr in tbody.find_all("tr"):
        cells = tr.find_all("td")
        if len(cells) < 5:
            continue
        rows.append({
            "Ex-Dividend Date": cells[0].get_text(strip=True),
            "Cash Amount": cells[1].get_text(strip=True),
            "Declaration Date": cells[2].get_text(strip=True),
            "Record Date": cells[3].get_text(strip=True),
            "Pay Date": cells[4].get_text(strip=True),
        })

    df = pd.DataFrame(rows)

    # 날짜 변환
    for col in ["Ex-Dividend Date", "Declaration Date", "Record Date", "Pay Date"]:
        df[col] = pd.to_datetime(df[col], format="%b %d, %Y", errors="coerce")

    # 배당금 숫자 처리
    df["Cash Amount"] = (
        df["Cash Amount"].str.replace("$", "", regex=False).str.replace(",", "", regex=False)
    )
    df["Cash Amount"] = pd.to_numeric(df["Cash Amount"], errors="coerce")

    # 정렬
    df = df.sort_values("Ex-Dividend Date", ascending=False).reset_index(drop=True)
    return df

# 기준일 가격 조회 (개별 수익률 계산용)
def get_price_for_dividend(ticker: str, div_date: pd.Timestamp) -> float:
    try:
        div_date = pd.to_datetime(div_date).tz_localize(None)  # ✅ 날짜도 명확히 비표준화

        ticker_obj = yf.Ticker(ticker)
        start = (div_date - pd.Timedelta(days=5)).strftime("%Y-%m-%d")
        end = (div_date + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
        hist = ticker_obj.history(start=start, end=end)

        if hist.empty:
            print(f"[{ticker}] ❌ 기준가 조회 실패: 데이터 없음")
            return None

        hist.index = hist.index.tz_localize(None)  # ✅ 인덱스도 표준화

        valid = hist[hist.index <= div_date]
        if not valid.empty:
            return valid["Close"].iloc[-1]
        return hist["Close"].iloc[0]
    except Exception as e:
        print(f"[{ticker}] ❌ 기준가 조회 실패: {e}")
        return None
