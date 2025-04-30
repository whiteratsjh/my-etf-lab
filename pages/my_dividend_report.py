import streamlit as st
import os
import json
import pandas as pd
import yfinance as yf  # 야후 파이낸스 API 사용
from datetime import datetime

# 데이터 파일 경로 설정 (상대 경로: ./data)
DATA_DIR = os.path.join(".", "data")
GROUPS_FILE = os.path.join(DATA_DIR, "my_dividend_report_groups.json")
TRANSACTIONS_FILE = os.path.join(DATA_DIR, "my_dividend_report_transactions.csv")

# ---------------------------
# 그룹 관리 관련 함수
# ---------------------------
def load_groups():
    if os.path.exists(GROUPS_FILE):
        try:
            with open(GROUPS_FILE, "r", encoding="utf-8") as f:
                groups = json.load(f)
            return groups
        except Exception as e:
            st.error(f"그룹 파일 로드 오류: {e}")
            return {}
    return {}

def save_groups(groups):
    try:
        with open(GROUPS_FILE, "w", encoding="utf-8") as f:
            json.dump(groups, f, ensure_ascii=False, indent=2)
    except Exception as e:
        st.error(f"그룹 파일 저장 오류: {e}")

# ---------------------------
# 거래 기록 관련 함수
# ---------------------------
def load_transactions():
    if not os.path.exists(TRANSACTIONS_FILE):
        return pd.DataFrame(columns=["날짜", "ETF Ticker", "현재원금", "당일배당금"])
    try:
        df = pd.read_csv(TRANSACTIONS_FILE)
        df["날짜"] = pd.to_datetime(df["날짜"])
        return df
    except Exception as e:
        st.error(f"거래 기록 로드 오류: {e}")
        return pd.DataFrame(columns=["날짜", "ETF Ticker", "현재원금", "당일배당금"])

def append_transaction(record):
    df_new = pd.DataFrame([record])
    mode = 'a' if os.path.exists(TRANSACTIONS_FILE) else 'w'
    header = not os.path.exists(TRANSACTIONS_FILE)
    try:
        df_new.to_csv(TRANSACTIONS_FILE, index=False, mode=mode, header=header)
    except Exception as e:
        st.error(f"거래 기록 저장 실패: {e}")

# ---------------------------
# 배당 포트폴리오 현황 스냅샷 생성 함수
# ---------------------------
def create_snapshot(trans_df):
    """
    거래 기록에서 각 티커별로 가장 최근의 원금, 누적 배당금, 회수율(누적배당금/원금×100)을 계산하고,
    yfinance를 통해 현재가를 조회한 후, 출력 시 
      - 현재가, 현재원금, 누적배당금: 소수점 4자리 (없으면 0.0000)
      - 회수율: 소수점 2자리 (없으면 0.00)
    로 포맷팅한다.
    """
    if trans_df.empty:
        return pd.DataFrame()
    snapshot = []
    grouped = trans_df.sort_values(by="날짜").groupby("ETF Ticker")
    for ticker, group in grouped:
        latest_record = group.iloc[-1]
        current_principal = latest_record["현재원금"]
        cumulative_dividend = group["당일배당금"].sum()
        yield_rate = (cumulative_dividend / current_principal * 100) if current_principal > 0 else 0.0
        try:
            price = yf.Ticker(ticker).info.get("regularMarketPrice")
        except Exception:
            price = None
        snapshot.append({
            "ETF Ticker": ticker,
            "현재가": price if price is not None else 0.0,
            "현재원금": current_principal,
            "누적배당금": cumulative_dividend,
            "회수율": yield_rate
        })
    df = pd.DataFrame(snapshot)
    # 각 열을 지정한 소수점 자릿수로 포맷팅 (문자열 형태로 출력)
    df["현재가"] = df["현재가"].apply(lambda x: f"{x:.4f}")
    df["현재원금"] = df["현재원금"].apply(lambda x: f"{x:.4f}")
    df["누적배당금"] = df["누적배당금"].apply(lambda x: f"{x:.4f}")
    df["회수율"] = df["회수율"].apply(lambda x: f"{x:.2f}")
    return df

# ---------------------------
# 페이지 렌더링 함수
# ---------------------------
def render_page():
    st.title("ETF 배당 리포트 관리 시스템")
    st.write("그룹 선택을 기준으로 배당 포트폴리오 현황 및 배당금 기록 조회를 확인하고, 하단에서 그룹 관리, 종목 관리, 거래 기록 등록을 할 수 있습니다.")

    # 최상단 그룹 선택 (그룹 변경시 자동 갱신)
    st.header("그룹 선택")
    groups = load_groups()
    if groups:
        selected_group_main = st.selectbox("그룹 선택", options=list(groups.keys()), key="main_group")
    else:
        st.info("먼저 그룹을 생성하세요.")
        selected_group_main = None

    # 1. 배당 포트폴리오 현황 (선택한 그룹)
    st.header("배당 포트폴리오 현황")
    if selected_group_main:
        transactions = load_transactions()
        group_tickers = groups.get(selected_group_main, [])
        if not transactions.empty:
            transactions_group = transactions[transactions["ETF Ticker"].isin(group_tickers)]
        else:
            transactions_group = transactions
        snapshot_df = create_snapshot(transactions_group)
        if not snapshot_df.empty:
            st.dataframe(snapshot_df)
        else:
            st.info("현재 상태 데이터를 확인할 수 없습니다.")
    else:
        st.info("배당 포트폴리오 현황을 보기 위해 그룹을 선택하세요.")

    # 2. 배당금 기록 조회 (선택한 그룹)
    st.header("배당금 기록 조회")
    if selected_group_main:
        transactions = load_transactions()
        group_tickers = groups.get(selected_group_main, [])
        transactions_group = transactions[transactions["ETF Ticker"].isin(group_tickers)]
        if not transactions_group.empty:
            current_year = datetime.today().year
            current_month = datetime.today().month
            col1, col2, col3 = st.columns(3)
            with col1:
                ticker_options = ["전체(All)"] + sorted(transactions_group["ETF Ticker"].unique().tolist())
                selected_ticker = st.selectbox("종목", options=ticker_options, index=0, key="record_ticker")
            with col2:
                year_filter = st.number_input("연도", value=current_year, step=1, key="record_year")
            with col3:
                month_filter = st.number_input("월", value=current_month, step=1, min_value=1, max_value=12, key="record_month")
            df_filtered = transactions_group.copy()
            if selected_ticker != "전체(All)":
                df_filtered = df_filtered[df_filtered["ETF Ticker"] == selected_ticker]
            df_filtered["연도"] = pd.to_datetime(df_filtered["날짜"]).dt.year
            df_filtered["월"] = pd.to_datetime(df_filtered["날짜"]).dt.month
            df_filtered = df_filtered[(df_filtered["연도"] == year_filter) & (df_filtered["월"] == month_filter)]
            if not df_filtered.empty:
                df_filtered["배당수익률"] = df_filtered.apply(
                    lambda row: (row["당일배당금"] / row["현재원금"] * 100) if row["현재원금"] > 0 else 0,
                    axis=1
                )
                df_display = df_filtered.rename(columns={"현재원금": "원금", "당일배당금": "배당금"})
                df_display["날짜"] = pd.to_datetime(df_display["날짜"]).dt.strftime("%Y-%m-%d")
                # 포맷팅: 원금, 배당금은 소수점 4자리, 배당수익률은 소수점 2자리
                df_display["원금"] = df_display["원금"].apply(lambda x: f"{x:.4f}")
                df_display["배당금"] = df_display["배당금"].apply(lambda x: f"{x:.4f}")
                df_display["배당수익률"] = df_display["배당수익률"].apply(lambda x: f"{x:.2f}")
                st.dataframe(df_display[["ETF Ticker", "날짜", "원금", "배당금", "배당수익률"]])
            else:
                st.info("해당 필터에 해당하는 배당 내역이 없습니다.")
        else:
            st.info("저장된 거래 기록이 없습니다.")
    else:
        st.info("배당금 기록 조회를 위해 그룹을 선택하세요.")

    # 3. 그룹 관리 (기본은 접힌 상태)
    st.header("그룹 관리")
    with st.expander("그룹 관리", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            new_group = st.text_input("새 그룹 이름", key="new_group")
            if st.button("그룹 추가", key="btn_add_group"):
                if not new_group:
                    st.warning("그룹 이름을 입력하세요.")
                elif new_group in groups:
                    st.warning("이미 존재하는 그룹입니다.")
                else:
                    groups[new_group] = []
                    save_groups(groups)
                    st.success(f"그룹 '{new_group}' 추가됨.")
        with col2:
            if groups:
                del_group = st.selectbox("삭제할 그룹 선택", options=list(groups.keys()), key="del_group")
                if st.button("그룹 삭제", key="btn_del_group"):
                    groups.pop(del_group)
                    save_groups(groups)
                    st.success(f"그룹 '{del_group}' 삭제됨.")
            else:
                st.info("등록된 그룹이 없습니다.")

    # 4. 종목 관리 (선택한 그룹)
    st.header("종목 관리")
    if selected_group_main:
        group_tickers = groups.get(selected_group_main, [])
        with st.expander("티커 추가/삭제", expanded=False):
            st.write(f"현재 '{selected_group_main}' 그룹 티커: {group_tickers}")
            with st.form("ticker_add_form", clear_on_submit=True):
                new_ticker = st.text_input("추가할 티커 (예: AAPL)", key="add_ticker")
                if st.form_submit_button("티커 추가"):
                    ticker = new_ticker.upper().strip()
                    if not ticker:
                        st.warning("티커를 입력하세요.")
                    elif ticker in group_tickers:
                        st.warning("이미 등록된 티커입니다.")
                    else:
                        group_tickers.append(ticker)
                        groups[selected_group_main] = group_tickers
                        save_groups(groups)
                        st.success(f"티커 {ticker} 추가됨.")
            with st.form("ticker_delete_form", clear_on_submit=True):
                if group_tickers:
                    del_ticker = st.selectbox("삭제할 티커 선택", options=group_tickers, key="delete_ticker")
                    if st.form_submit_button("티커 삭제"):
                        group_tickers.remove(del_ticker)
                        groups[selected_group_main] = group_tickers
                        save_groups(groups)
                        st.success(f"티커 {del_ticker} 삭제됨.")
                else:
                    st.info("등록된 티커가 없습니다.")
                    st.form_submit_button("확인")
    else:
        st.info("종목 관리를 위해 그룹을 선택하세요.")

    # 5. 거래 기록 등록 (선택한 그룹)
    st.header("거래 기록 등록")
    if selected_group_main:
        with st.expander("거래 기록 등록", expanded=False):
            with st.form("transaction_form", clear_on_submit=True):
                trans_date = st.date_input("거래 날짜", value=datetime.today(), key="trans_date")
                # 선택한 그룹에 등록된 티커만 표시
                tickers = groups.get(selected_group_main, [])
                if tickers:
                    ticker_trans = st.selectbox("티커 선택", options=tickers, key="trans_ticker")
                else:
                    ticker_trans = st.text_input("티커 (등록된 티커 없음)", key="trans_ticker_input")
                current_principal = st.number_input("현재 원금", min_value=0.0, step=0.0001, format="%.4f", key="current_principal")
                daily_dividend = st.number_input("당일 배당금", min_value=0.0, step=0.0001, format="%.4f", key="daily_dividend")
                if st.form_submit_button("거래 기록 저장"):
                    if current_principal <= 0:
                        st.warning("현재 원금은 0보다 커야 합니다.")
                    elif not ticker_trans:
                        st.warning("티커를 선택 또는 입력하세요.")
                    else:
                        record = {
                            "날짜": trans_date.strftime("%Y-%m-%d"),
                            "ETF Ticker": ticker_trans.upper().strip(),
                            "현재원금": current_principal,
                            "당일배당금": daily_dividend
                        }
                        append_transaction(record)
                        st.success("거래 기록이 저장되었습니다.")
                        st.experimental_rerun()  # 기록 저장 후 페이지 재실행하여 조회 내용을 갱신
    else:
        st.info("거래 기록 등록을 위해 그룹을 선택하세요.")

if __name__ == "__main__":
    render_page()