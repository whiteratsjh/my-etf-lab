import streamlit as st
import os
import json
import datetime
import pandas as pd
import numpy as np
import yfinance as yf
import logging
import time
import altair as alt

# 설정: 데이터, 로그, 파일 만료 기간 등
DATA_DIR = os.path.join("d:\\project\\my-etf-lab", "data")
STOCK_DATA_DIR = os.path.join(DATA_DIR, "stock_data")
STOCK_INSIGHT_DIR = os.path.join(DATA_DIR, "stock_insight")
FAVORITE_FILE = os.path.join(DATA_DIR, "favorite.json")
FILE_EXPIRY_DAYS = 7
TODAY_STR = datetime.datetime.today().strftime("%Y%m%d")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s:%(message)s")

# 디렉토리 생성
for d in [DATA_DIR, STOCK_DATA_DIR, STOCK_INSIGHT_DIR]:
    if not os.path.exists(d):
        os.makedirs(d)

####################
# 즐겨찾기 파일 관리
####################
def load_favorites():
    if os.path.exists(FAVORITE_FILE):
        try:
            with open(FAVORITE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            st.error("즐겨찾기 데이터를 읽는 중 오류가 발생했습니다.")
            return {}
    else:
        return {}

def save_favorites(favorites):
    with open(FAVORITE_FILE, "w", encoding="utf-8") as f:
        json.dump(favorites, f, ensure_ascii=False, indent=2)

####################
# 파일 유효성 체크: 1주일 초과 파일 삭제
####################
def is_file_expired(file_path):
    if os.path.exists(file_path):
        mtime = os.path.getmtime(file_path)
        file_date = datetime.datetime.fromtimestamp(mtime)
        return (datetime.datetime.now() - file_date).days >= FILE_EXPIRY_DAYS
    return True

def cleanup_old_files(folder):
    for fname in os.listdir(folder):
        fpath = os.path.join(folder, fname)
        if os.path.isfile(fpath) and is_file_expired(fpath):
            os.remove(fpath)
            logging.info(f"Deleted expired file: {fpath}")

####################
# 주식 데이터 가져오기 및 저장
####################
def get_stock_data(ticker):
    cleanup_old_files(STOCK_DATA_DIR)
    file_path = os.path.join(STOCK_DATA_DIR, f"{ticker}_{TODAY_STR}.csv")
    if os.path.exists(file_path):
        df = pd.read_csv(file_path, index_col="Date", parse_dates=True)
        logging.info(f"Using cached data for {ticker} from {file_path}")
    else:
        # 3년치 데이터 다운로드: yf.Ticker(ticker).history 사용
        ticker_obj = yf.Ticker(ticker)
        df = ticker_obj.history(period="3y")
        if df.empty:
            st.warning(f"{ticker}의 데이터를 가져오지 못했습니다.")
            return None
        df.to_csv(file_path)
        logging.info(f"Saved new data for {ticker} to {file_path}")
    return df

####################
# 지표 계산
####################
def calculate_indicators(df):
    indicators = {}
    # 이동평균 계산 (MA20, MA125, MA200)
    df["MA20"] = df["Close"].rolling(window=20).mean()
    df["MA125"] = df["Close"].rolling(window=125).mean()
    df["MA200"] = df["Close"].rolling(window=200).mean()
    
    # 전체기간 수익률 계산
    start_price = df["Close"].iloc[0]
    end_price = df["Close"].iloc[-1]
    overall_return = (end_price / start_price - 1) * 100
    indicators["전체변동률평균"] = overall_return
    
    # 수익률 및 표준편차 계산
    df["Return"] = df["Close"].pct_change()
    std_return = df["Return"].std() * 100
    indicators["표준편차"] = std_return
    indicators["-1 시그마"] = -1 * std_return
    indicators["-2 시그마"] = -2 * std_return
    indicators["-3 시그마"] = -3 * std_return
    
    # RSI 계산 (단순)
    delta = df["Close"].diff()
    gain = delta.clip(lower=0).rolling(window=14).mean()
    loss = -delta.clip(upper=0).rolling(window=14).mean()
    RS = gain / loss
    RSI = 100 - (100 / (1 + RS))
    indicators["RSI"] = RSI.iloc[-1] if not RSI.empty else np.nan
    
    # 스토캐스틱 계산 (단순)
    low_min = df["Low"].rolling(window=14).min()
    high_max = df["High"].rolling(window=14).max()
    stoch = 100 * ((df["Close"] - low_min) / (high_max - low_min))
    indicators["Stoch"] = stoch.iloc[-1] if not stoch.empty else np.nan
    
    # 조합지표 계산
    indicators["RSI-Stoch"] = (indicators["RSI"] + indicators["Stoch"]) / 2 \
                               if not np.isnan(indicators["RSI"]) and not np.isnan(indicators["Stoch"]) \
                               else np.nan
    
    # 이동평균선 값 저장
    indicators["MA20"] = df["MA20"].iloc[-1]
    indicators["MA125"] = df["MA125"].iloc[-1]
    indicators["MA200"] = df["MA200"].iloc[-1]
    
    # 이격도 계산 (%)
    current_price = df["Close"].iloc[-1]
    indicators["단기이격도"] = (current_price - indicators["MA20"]) / indicators["MA20"] * 100
    indicators["중기이격도"] = (current_price - indicators["MA125"]) / indicators["MA125"] * 100
    indicators["장기이격도"] = (current_price - indicators["MA200"]) / indicators["MA200"] * 100
    
    return indicators

def interpret_gap_signal(gap, label):
    # gap: 이격도 값, label: "단기", "중기", "장기"
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
    # HTML 적용: label, signal, 수치 (소수점 1자리)
    return f"{label}: <span style='color:{color};'>{signal}</span> ({gap_r:+.1f}%)"

def interpret_aux_signal(value, label):
    # 보조지표 개별 해석: value: RSI 등, label: "RSI", "Stoch", "RSI-Stoch"
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

####################
# 주식 인사이트 저장
####################
def save_stock_insight(ticker, indicators):
    cleanup_old_files(STOCK_INSIGHT_DIR)
    file_path = os.path.join(STOCK_INSIGHT_DIR, f"{ticker}_{TODAY_STR}.csv")
    df_insight = pd.DataFrame([indicators])
    df_insight.to_csv(file_path, index=False)
    logging.info(f"Saved stock insight for {ticker} to {file_path}")

####################
# 스트림릿 UI 구성 함수들
####################
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
        # 티커 추가 가능 개수를 20개로 확장
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


def get_gap_signal_text(gap, label):
    gap_r = round(gap, 1)
    
    # 이격도 기준 설정
    if label == "단기":
        threshold = 5
    elif label == "중기":
        threshold = 10
    elif label == "장기":
        threshold = 15
    else:
        threshold = 10  # 디폴트
    
    # 신호 판단
    if gap >= threshold:
        signal = "매도"
    elif gap <= -threshold:
        signal = "매수"
    else:
        signal = "중립"
    
    return f"{label}: {signal} ({gap_r:+.1f}%)"

def get_aux_signal_text(value, label):
    # value: 보조지표 값, label: "RSI", "Stoch", "RSI-Stoch"
    val_r = round(value, 1)
    if value < 30:
        signal = "매수"
    elif value > 70:
        signal = "매도"
    else:
        signal = "중립"
    # 반환 예: "RSI: 매수 (28.5)"
    return f"{label}: {signal} ({val_r:.1f})"

def color_aux(val):
    # 보조지표 수치에 대해 색상 적용: 30 이하 → blue, 70 이상 → red, 그 외는 기본색
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
        # 📈 이격도 신호: 슬래시("/")로 구분 (텍스트에는 색상 적용X)
        gap_short = get_gap_signal_text(indicators.get("단기이격도", 0), "단기")
        gap_mid   = get_gap_signal_text(indicators.get("중기이격도", 0), "중기")
        gap_long  = get_gap_signal_text(indicators.get("장기이격도", 0), "장기")
        entry["📈 이격도 신호"] = f"{gap_short} / {gap_mid} / {gap_long}"
        
        # 🧭 보조지표 신호: 슬래시("/")로 구분 (텍스트 자체에 색상 없음)
        aux_rsi = get_aux_signal_text(indicators.get("RSI", np.nan), "RSI")
        aux_stoch = get_aux_signal_text(indicators.get("Stoch", np.nan), "Stoch")
        aux_rsistoch = get_aux_signal_text(indicators.get("RSI-Stoch", np.nan), "RSI-Stoch")
        entry["🧭 보조지표 신호"] = f"{aux_rsi} / {aux_stoch} / {aux_rsistoch}"
        
        metrics_list.append(entry)
    
    if metrics_list:
        df_metrics = pd.DataFrame(metrics_list)
        # 최종 컬럼 순서 지정
        df_metrics = df_metrics[[ 
            "티커", "종목명", "현재가", "변동률(%)", "표준편차(%)",
            "-1 시그마", "-2 시그마", "-3 시그마",
            "RSI", "Stoch", "RSI-Stoch",
            "MA20", "MA125", "MA200",
            "📈 이격도 신호", "🧭 보조지표 신호"
        ]]
        # Pandas Styler: 보조지표 수치 컬럼(RSI, Stoch, RSI-Stoch)만 조건부 색상 적용
        styled = (df_metrics.style
                  .applymap(color_aux, subset=["RSI", "Stoch", "RSI-Stoch"])
                  .hide(axis="index"))
        st.dataframe(styled, use_container_width=True)
    else:
        st.info("지표를 계산할 수 있는 데이터가 없습니다.")


def render_price_chart(favorites, selected_group):
    st.subheader("최근 가격 변동 (정규화)")
    group_tickers = favorites.get(selected_group, [])
    if not group_tickers:
        st.info("티커가 없으므로 차트를 표시할 수 없습니다.")
        return

    # 기간 선택: 라디오 버튼 (기본 "3개월")
    period_options = {"1개월": 30, "3개월": 90, "6개월": 180, "1년": 365}
    selected_period_label = st.radio(
        "기간 선택", options=list(period_options.keys()), index=1
    )
    period_days = period_options[selected_period_label]

    # 종목 선택: multiselect (기본은 그룹 내 모든 티커)
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
        # 정규화: 첫날 기준으로 변화량 계산
        norm_price = df_recent - df_recent.iloc[0]
        norm_price = norm_price.reset_index()  # Date 열 생성
        norm_price["ticker"] = ticker
        chart_df = pd.concat([chart_df, norm_price], ignore_index=True)
        
    if chart_df.empty:
        st.info("선택한 기간에 대해 충분한 데이터가 없습니다.")
        return

    # Altair 차트 생성; legend 다중 선택 지원
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

def get_aux_signal_insight(value, label):
    """보조지표 해석: 30 이하 → 과매도, 70 이상 → 과열, 그 외는 중립"""
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
        # 현재 데이터(마지막 행) 기준 계산
        ma20 = df["Close"].rolling(window=20).mean().iloc[-1]
        std20 = df["Close"].rolling(window=20).std().iloc[-1]
        upper = ma20 + 2 * std20
        lower = ma20 - 2 * std20
        close = df["Close"].iloc[-1]

        # 1. 중앙 위치 판정 (MA20 대비 % 차이)
        rel_diff = (close - ma20) / ma20 * 100
        if abs(rel_diff) <= 1:
            center_pos = "중심선 부근"
        elif rel_diff > 1:
            center_pos = "중심선 위"
        else:
            center_pos = "중심선 아래"

        # 2. 밴드 폭 계산 (%)
        band_width = (upper - lower) / ma20 * 100
        if band_width <= 5:
            band_desc = "밴드 폭 매우 좁음"
        elif band_width <= 10:
            band_desc = "밴드 폭 적당"
        else:
            band_desc = "밴드 폭 넓음"

        # 3. 최근 5일 전 밴드 폭과 비교하여 변화 추세 판정
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

        # 4. 최종 해석 (예시 기준)
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
    """각 종목별 주요 지표 해석 텍스트를 생성하고 복사할 수 있도록 출력"""
    st.subheader("종목별 인사이트 요약")
    group_tickers = favorites.get(selected_group, [])
    if not group_tickers:
        st.info("인사이트를 출력할 종목이 없습니다.")
        return

    # 인사이트 텍스트를 저장할 리스트 (티커명 기준 오름차순)
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

        # 기본 항목: 티커, 현재가, 전체변동률
        summary = f"티커: {ticker}  현재가: {round(current_price,2)} USD  전체 변동률: {round(indicators.get('전체변동률평균',np.nan),1):+.1f}%\n"
        # 이격도 신호 (get_gap_signal_text() 함수 사용 → 단기: MA20, 중기: MA125, 장기: MA200)
        gap_short = get_gap_signal_text(indicators.get("단기이격도", 0), "단기")
        gap_mid   = get_gap_signal_text(indicators.get("중기이격도", 0), "중기")
        gap_long  = get_gap_signal_text(indicators.get("장기이격도", 0), "장기")
        summary += f"[이격도 신호] {gap_short}  {gap_mid}  {gap_long}\n"
        # 보조지표 신호 (새 함수 get_aux_signal_insight() 사용)
        aux_rsi = get_aux_signal_insight(indicators.get("RSI", np.nan), "RSI")
        aux_stoch = get_aux_signal_insight(indicators.get("Stoch", np.nan), "Stoch")
        aux_rsistoch = get_aux_signal_insight(indicators.get("RSI-Stoch", np.nan), "RSI-Stoch")
        summary += f"[보조지표 신호] {aux_rsi}  {aux_stoch}  {aux_rsistoch}\n"
        # 볼린저밴드 인사이트 (계산 후 해석)
        bollinger = get_bollinger_insight(df)
        summary += f"[볼린저밴드] {bollinger}\n"
        # 빈 줄 추가
        insights.append(summary)

    if insights:
        full_text = "\n".join(insights)
        # 고정폭 글꼴의 코드 블록 스타일로 출력 (st.code 사용)
        st.code(full_text, language="text")
        # 복사 다운로드 버튼: 텍스트 그대로 복사 가능
        st.download_button("인사이트 텍스트 복사", full_text, file_name="insights.txt", mime="text/plain")
    else:
        st.info("종목별 인사이트를 생성할 데이터가 없습니다.")

####################
# 메인 앱 함수 (스트림릿 UI 전체 구성)
####################
def main():
    st.title("관심종목 페이지")
    favorites = load_favorites()
    render_group_management(favorites)
    
    st.subheader("관심그룹 선택")
    groups = list(favorites.keys())
    if not groups:
        st.info("먼저 관심그룹을 추가해주세요.")
        return
    selected_group = st.selectbox("관심그룹", groups)
    
    render_ticker_addition(favorites, selected_group)
    render_metrics_table(favorites, selected_group)
    render_price_chart(favorites, selected_group)
    render_insights_text(favorites, selected_group)

if __name__ == "__main__":
    main()

def render():
    main()