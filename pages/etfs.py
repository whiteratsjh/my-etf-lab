import streamlit as st
import yfinance as yf
import plotly.express as px
import numpy as np
import streamlit.components.v1 as components
import plotly.graph_objects as go
import pandas as pd
from plotly.subplots import make_subplots

def add_fibonacci_lines(fig, high, low, current_price):
    fib_levels = [0.0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0]
    # 각 레벨 가격 계산
    fib_prices = [low + (high - low) * level for level in fib_levels]
    fib_prices = sorted(fib_prices)

    # current_price가 포함된 인접 피보나치 가격 구간 찾기
    fill_lower = None
    fill_upper = None
    for i in range(len(fib_prices) - 1):
        if fib_prices[i] <= current_price <= fib_prices[i + 1]:
            fill_lower = fib_prices[i]
            fill_upper = fib_prices[i + 1]
            break

    # 현재가가 포함된 영역에 아이보리 색 사각형 추가 (layer="above"로 설정)
    if fill_lower is not None and fill_upper is not None:
        print(f"Fibonacci levels: {fib_prices}")
        print(f"Current price: {current_price}")
        print("fill 영역:", fill_lower, "~", fill_upper)

        fig.add_shape(
            type="rect",
            xref="x",  # 실시간 날짜 축 기준
            yref="y",
            x0=fig.data[0].x[0],
            x1=fig.data[0].x[-1],
            y0=fill_lower,
            y1=fill_upper,
            fillcolor="rgba(255, 255, 200, 0.4)",  # 더 진한 색 (연노랑 느낌)
            line_width=0,
            layer="above"
        )


    # 피보나치 수평선 추가
    for level, price in zip(fib_levels, fib_prices):
        fig.add_hline(
            y=price,
            line_dash="dot",
            line_color="gray",
            annotation_text=f"Fib {level:.3f}",
            annotation_position="top left",
            opacity=0.5,
        )
    return fig

# 보조지표 계산 함수들
def calculate_rsi(series, period):
    delta = series.diff()
    up = delta.clip(lower=0)
    down = -delta.clip(upper=0)
    ma_up = up.rolling(window=period).mean()
    ma_down = down.rolling(window=period).mean()
    rs = ma_up / ma_down
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_macd(series, fast=12, slow=26, signal=9):
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram

def calculate_stochastic(series, period=14):
    low_min = series.rolling(window=period).min()
    high_max = series.rolling(window=period).max()
    stoch = (series - low_min) / (high_max - low_min) * 100
    return stoch

def render():
    st.header("📘 ETF 장기 투자자 분석")
    
    ticker = st.text_input("티커 입력 (예: SCHD)", "SCHD", key="etf_input")
    
    if ticker:
        try:
            ticker_obj = yf.Ticker(ticker)
            # 3년치 데이터 조회 (여유 있게 데이터 확보)
            data_full = ticker_obj.history(period="3y")
            if data_full.empty:
                st.warning("해당 종목의 데이터를 불러올 수 없습니다.")
                st.stop()
            # 화면 표시용: 최근 1년치 데이터 (약 252거래일)
            chart_data = data_full.tail(252)
            
            info = ticker_obj.info
            name = info.get("shortName", ticker.upper())
            quote_type = info.get("quoteType", "Unknown")
            exchange = info.get("exchange", "Unknown")
            
            # 기본 가격 데이터
            close = chart_data["Close"]
            current_price = close.iloc[-1]
            
            # 이동평균선 계산 (chart_data 기간 기준)
            ma10 = data_full["Close"].rolling(window=10).mean().iloc[-len(chart_data):]
            ma50 = data_full["Close"].rolling(window=50).mean().iloc[-len(chart_data):]
            ma200 = data_full["Close"].rolling(window=200).mean().iloc[-len(chart_data):]
            
            # 볼린저밴드 계산 (20일, 표준편차 2)
            ma20 = data_full["Close"].rolling(window=20).mean().iloc[-len(chart_data):]
            std20 = data_full["Close"].rolling(window=20).std().iloc[-len(chart_data):]
            upper_band = ma20 + 2 * std20
            lower_band = ma20 - 2 * std20
            
            # 메인 차트: 가격 + MA, 볼린저밴드 추가
            fig = px.line(chart_data, x=chart_data.index, y="Close", title=f"{name} 1년 가격 추이")
            fig.update_layout(height=600, dragmode="zoom",
                              margin=dict(l=40, r=40, t=40, b=40))
            
            fig.add_scatter(x=chart_data.index, y=ma10, mode="lines", name="MA10",
                            line=dict(color="orange", width=2))
            fig.add_scatter(x=chart_data.index, y=ma50, mode="lines", name="MA50",
                            line=dict(color="purple", width=2))
            fig.add_scatter(x=chart_data.index, y=ma200, mode="lines", name="MA200",
                            line=dict(color="blue", width=2))
            
            # 볼린저밴드는 상단, 하단, 중앙(MA20) 그리고 영역 채우기
            fig.add_scatter(x=chart_data.index, y=upper_band, mode="lines", name="Upper BB",
                            line=dict(color="lightblue", width=1))
            fig.add_scatter(x=chart_data.index, y=lower_band, mode="lines", name="Lower BB",
                            line=dict(color="lightblue", width=1),
                            fill="tonexty", fillcolor="rgba(200,200,255,0.2)")
            fig.add_scatter(x=chart_data.index, y=ma20, mode="lines", name="MA20 (BB)",
                            line=dict(color="grey", width=1, dash="dash"))
            
            st.plotly_chart(fig, use_container_width=True, config={"scrollZoom": True})
            
            # -----------------
            # 하단 보조지표 계산 및 subplot 시각화
            rsi28 = calculate_rsi(chart_data["Close"], 28)
            macd_line, signal_line, hist = calculate_macd(chart_data["Close"])
            stoch_k = calculate_stochastic(chart_data["Close"], period=14)
            stoch_d = stoch_k.rolling(window=3).mean()
            
            fig_ind = make_subplots(rows=3, cols=1,
                                    shared_xaxes=True,
                                    vertical_spacing=0.05,
                                    subplot_titles=["MACD (12,26,9)", "RSI(28)", "Stochastic Slow (14,3,3)"])
            # MACD subplot
            fig_ind.add_trace(go.Scatter(x=chart_data.index, y=macd_line,
                                         mode="lines", name="MACD"), row=1, col=1)
            fig_ind.add_trace(go.Scatter(x=chart_data.index, y=signal_line,
                                         mode="lines", name="Signal"), row=1, col=1)
            fig_ind.add_trace(go.Bar(x=chart_data.index, y=hist,
                                     name="Histogram", marker_color="grey"), row=1, col=1)
            # RSI(28) subplot
            fig_ind.add_trace(go.Scatter(x=chart_data.index, y=rsi28,
                                         mode="lines", name="RSI(28)"), row=2, col=1)
            fig_ind.add_hline(y=70, line_dash="dot", line_color="red", row=2, col=1)
            fig_ind.add_hline(y=30, line_dash="dot", line_color="green", row=2, col=1)
            # Stochastic Slow subplot
            fig_ind.add_trace(go.Scatter(x=chart_data.index, y=stoch_k,
                                         mode="lines", name="Stoch %K"), row=3, col=1)
            fig_ind.add_trace(go.Scatter(x=chart_data.index, y=stoch_d,
                                         mode="lines", name="Stoch %D"), row=3, col=1)
            fig_ind.add_hline(y=80, line_dash="dot", line_color="red", row=3, col=1)
            fig_ind.add_hline(y=20, line_dash="dot", line_color="green", row=3, col=1)
            
            fig_ind.update_layout(height=850, title_text="보조지표 분석", showlegend=True,
                                  margin=dict(l=40, r=40, t=60, b=40))
            st.plotly_chart(fig_ind, use_container_width=True, config={"scrollZoom": True})
            
            # -----------------
            # 종목 기본 정보 및 일간 등락률 계산
            prev_close = close.shift(1)
            daily_return = ((current_price - prev_close.iloc[-1]) / prev_close.iloc[-1]) * 100
            returns = close.pct_change().dropna()
            mean_return = returns.mean() * 100
            std_return = returns.std() * 100
            n_sigma = (daily_return - mean_return) / std_return if std_return != 0 else 0

            # 각 보조지표의 현재값
            macd_now = macd_line.iloc[-1]
            signal_now = signal_line.iloc[-1]
            hist_now = hist.iloc[-1]
            rsi28_now = rsi28.iloc[-1]
            stoch_k_now = stoch_k.iloc[-1]
            stoch_d_now = stoch_d.iloc[-1]
            ma10_now = ma10.iloc[-1]
            ma50_now = ma50.iloc[-1]
            ma200_now = ma200.iloc[-1]
            upper_now = upper_band.iloc[-1]
            ma20_now = ma20.iloc[-1]
            lower_now = lower_band.iloc[-1]

            # ----------------- 최종 인사이트 섹션 -----------------

            # 1. 52주 고점/저점, 최근 20일 고점 및 최근 20일 저점 계산 (data_full 이용)
            week52_high = data_full["Close"].max()
            week52_low = data_full["Close"].min()
            recent20_high = chart_data["Close"].tail(20).max()
            recent20_low = chart_data["Close"].tail(20).min()

            # 2. MDD 및 회복률 계산
            mdd_52week = (current_price - week52_high) / week52_high * 100
            mdd_recent20 = (current_price - recent20_high) / recent20_high * 100
            recovery_from_low = (current_price - week52_low) / week52_low * 100
            recovery_recent20 = (current_price - recent20_low) / recent20_low * 100

            # 3. 피보나치 분석 (52주 기준)
            fib_levels = [0.0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0]
            fib_prices = [week52_low + (week52_high - week52_low) * level for level in fib_levels]
            zone = ""
            for i in range(len(fib_prices)-1):
                if fib_prices[i] <= current_price <= fib_prices[i+1]:
                    zone = f"Fib {fib_levels[i]:.3f} ~ {fib_levels[i+1]:.3f}"
                    break
            if not zone:
                zone = "범위 외"

            # 4. 가치투자 시나리오 (예시)
            if current_price < week52_high * 0.8:
                val_msg = "현재 가격이 52주 고점 대비 약 20% 할인되어 있습니다."
            elif current_price > week52_high * 0.95:
                val_msg = "현재 가격이 52주 고점에 근접하여 단기 조정 가능성이 있습니다."
            else:
                val_msg = "현재 가격은 중간 수준으로, 신중한 접근이 필요합니다."

            # 종목 기본 정보 및 σ 위치
            summary_info = f"""📌 종목: {ticker.upper()} ({name})
현재가: ${current_price:.2f}
최근 일간 등락률: {daily_return:+.2f}%
평균 일등락률(μ): {mean_return:+.2f}%, 표준편차(σ): {std_return:.2f}% → **{n_sigma:+.1f}σ**
"""

            # 기술적 해석 (기존 지표값 활용)
            technical_insight = f"""📊 **기술적 해석**
- MACD: {macd_now:+.2f} (Signal: {signal_now:+.2f}, Histogram: {hist_now:+.2f})
- RSI(28): {rsi28_now:.1f} → {"과매도" if rsi28_now < 30 else ("과매수" if rsi28_now > 70 else "중립")}
- Stochastic Slow: %K={stoch_k_now:.1f}, %D={stoch_d_now:.1f} → {"과매도" if stoch_k_now < 20 else ("과매수" if stoch_k_now > 80 else "중립")}
- 이동평균선: MA10={ma10_now:.2f}, MA50={ma50_now:.2f}, MA200={ma200_now:.2f}
   → { "장기 상승 흐름 유지" if current_price > ma10_now > ma50_now > ma200_now else ("MA200 하회" if current_price < ma200_now else "추세 전환 모호") }
- 골든/데드 크로스: { "골든크로스 발생" if ma50_now > ma200_now else "데드크로스 발생" }
- 볼린저밴드: 상단={upper_now:.2f}, 중앙(MA20)={ma20_now:.2f}, 하단={lower_now:.2f} → 현재가 { "상단" if current_price>upper_now else ("하단" if current_price<lower_now else "중앙") }
   → { "볼린저밴드 수축 발생" if (upper_band - lower_band).tail(5).mean() < (upper_band - lower_band).iloc[-10:-5].mean() else "수축 미발생" }
👉 기술적으로는 **관망 또는 확인 필요** 상태입니다.
"""

            # MDD 및 회복률 분석
            mdd_info = f"""📈 **MDD 및 회복률 분석**
- 52주 고점 대비: {mdd_52week:+.1f}%
- 최근 20일 고점 대비: {mdd_recent20:+.1f}%
- 52주 저점 대비 회복률: {recovery_from_low:+.1f}%
- 최근 20일 저점 대비 회복률: {recovery_recent20:+.1f}%
"""

            # 피보나치 분석
            fib_insight = f"""🧮 **피보나치 분석**
- 기준: 52주 고점 ${week52_high:.2f}, 52주 저점 ${week52_low:.2f}
- 현재가 ${current_price:.2f}는 {zone} 구간에 위치
→ 다음 저항: Fib 0.618 구간 (예상 가격: ${(week52_low + (week52_high - week52_low)*0.618):.2f})
"""

            # 가치투자 시나리오
            value_insight = f"""💡 **가치투자 시나리오**
- 52주 고점: ${week52_high:.2f}, 현재가: ${current_price:.2f}
- {val_msg}
👉 장기 가치 관점에서는 **저가 매수 또는 분할 매집 전략**을 고려할 만합니다.
"""

            # ----------------- 배당/수익률 통계 섹션 추가 -----------------

            # 최근 1년간 배당 총액 계산 (dividends Series는 날짜 인덱스)
            one_year_ago = pd.Timestamp.today(tz='America/New_York') - pd.DateOffset(years=1)
            dividends_last_year = ticker_obj.dividends[ticker_obj.dividends.index >= one_year_ago].sum()

            # 시가 배당률 계산: (최근 1년 배당총액 ÷ 현재 주가 × 100)
            dividend_yield = dividends_last_year / current_price * 100

            # 평균 일수익률 및 수익률 표준편차 계산 (백분율)
            avg_daily_return = close.pct_change().mean() * 100
            std_daily_return = close.pct_change().std() * 100

            # Sharpe Ratio (단순 계산): (평균 일수익률 - 0.1) ÷ 일수익률 표준편차
            sharpe_ratio = (avg_daily_return - 0.1) / std_daily_return if std_daily_return != 0 else None

            dividend_info = f"""📊 배당/수익률 통계 요약
- 현재 주가: ${current_price:.2f}
- 최근 1년간 배당 총액: ${dividends_last_year:.4f}
- 시가 배당률: {dividend_yield:.2f}%
- 평균 일수익률: {avg_daily_return:.3f}%
- 수익률 표준편차: {std_daily_return:.3f}%
- Sharpe Ratio (단순): {sharpe_ratio:.3f}
"""

            if sharpe_ratio is not None and sharpe_ratio < 0:
                dividend_info += "\n=> 리스크 대비 수익이 비효율적입니다."

            # 최종 출력 (모든 섹션 분리) - 순서 조정
            st.markdown(summary_info)
            st.markdown(technical_insight)
            st.markdown(mdd_info)
            st.markdown(fib_insight)
            st.markdown(value_insight)
            st.markdown(dividend_info + """\n\n⚠️ 참고: Sharpe Ratio는 배당을 반영하지 않으므로, 고배당 ETF에선 낮아도 큰 의미는 없습니다.""")
            st.caption("※ 본 분석은 투자 참고용이며, 매수/매도 추천이 아닙니다. 투자 판단은 투자자 본인의 책임입니다.")
            
        except Exception as e:
            st.error(f"데이터 로드 실패: {e}")

