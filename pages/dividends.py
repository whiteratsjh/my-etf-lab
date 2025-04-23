import streamlit as st
import pandas as pd
from utils.data_utils import get_etf_dividend_data, fetch_price, get_price_for_dividend

def render():
    st.header("📈 배당 정보")

    ticker_input = st.text_input("ETF 티커 (예: SCHD)", "SCHD")

    if ticker_input:
        try:
            with st.spinner("📆 배당 데이터를 불러오는 중... 잠시만 기다려주세요."):
                df = get_etf_dividend_data(ticker_input.strip())

            if df.empty:
                st.warning("배당 데이터가 없습니다.")
                st.stop()

            current_price = fetch_price(ticker_input.strip())

            # 최근 1년간 배당금 합산 및 시가배당율 계산
            temp_df = df.copy()
            temp_df["Ex-Dividend Date"] = pd.to_datetime(temp_df["Ex-Dividend Date"], errors="coerce")
            one_year_ago = pd.Timestamp.now() - pd.DateOffset(years=1)
            recent_dividends = temp_df[temp_df["Ex-Dividend Date"] >= one_year_ago]
            total_dividend = recent_dividends["Cash Amount"].sum()
            yield_percent = (total_dividend / current_price * 100) if current_price else 0.0

            col1, col2 = st.columns([3, 1])
            with col2:
                st.markdown(
                    f"<div style='white-space: nowrap; font-weight: bold;'>현재 가격: {current_price:.2f} (시가배당율: {yield_percent:.1f}%)</div>",
                    unsafe_allow_html=True
                )

            # Reference Price, Yield (%) 계산 (기준가격을 소수점 4자리 문자열 형식으로 포맷)
            df["Reference Price"] = df["Ex-Dividend Date"].apply(
                lambda d: get_price_for_dividend(ticker_input.strip(), d)
            )
            df["Yield (%)"] = df.apply(
                lambda row: round((row["Cash Amount"] / row["Reference Price"] * 100), 2)
                if pd.notna(row["Reference Price"]) and row["Reference Price"] != 0 else None,
                axis=1
            )
            # Reference Price를 소수점 4자리까지 반올림 후 문자열 형식으로 변환
            df["Reference Price"] = df["Reference Price"].round(4)
            df["Reference Price"] = df["Reference Price"].apply(lambda x: f"{x:.4f}" if pd.notna(x) else None)

            # 날짜 컬럼들을 YYYY-MM-DD 형식으로 변환
            date_cols = ["Ex-Dividend Date", "Declaration Date", "Record Date", "Pay Date"]
            for col in date_cols:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors="coerce").dt.strftime("%Y-%m-%d")

            # 컬럼명 한글화
            df.rename(columns={
                "Ex-Dividend Date": "배당락일",
                "Cash Amount": "배당금",
                "Declaration Date": "선언일",
                "Record Date": "기록일",
                "Pay Date": "지급일",
                "Reference Price": "기준가격 ($)",
                "Yield (%)": "배당수익률 (%)"
            }, inplace=True)

            # 배당수익률 (%) 컬럼을 소수점 2자리 문자열로 변환
            df["배당수익률 (%)"] = df["배당수익률 (%)"].apply(lambda x: f"{x:.2f}" if pd.notna(x) else None)

            # "기준가격 ($)" 컬럼 우측 정렬 적용 – 전체 셀에 대해 우측 정렬
            styled_df = df.style.set_properties(**{'text-align': 'right'})

            # 테이블의 너비를 100%로 설정 (HTML 테이블 태그에 style 속성 추가)
            html_table = styled_df.to_html()
            html_table = html_table.replace("<table", '<table style="width:100%;"')

            st.markdown(html_table, unsafe_allow_html=True)

            # 하단에 평단가 입력 및 YOC 계산 기능 추가
            st.markdown("---")
            st.markdown("### 내 평단가 입력 및 YOC 계산")
            avg_price = st.number_input("평단가를 입력하세요 (예: 50.00)", min_value=0.0, format="%.2f")
            if avg_price > 0:
                my_yoc = (total_dividend / avg_price) * 100
                st.markdown(
                    f"<div style='white-space: nowrap; font-weight: bold;'>내 YOC: {my_yoc:.1f}%</div>",
                    unsafe_allow_html=True
                )

        except Exception as e:
            st.error(f"배당 데이터를 불러오는데 실패했습니다: {e}")
