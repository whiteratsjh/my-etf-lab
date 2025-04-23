import streamlit as st
import streamlit.components.v1 as components
import plotly.express as px
import yfinance as yf
from utils.data_utils import fetch_price

def get_change(ticker):
    try:
        data = yf.Ticker(ticker).history(period="7d")
        if not data.empty and len(data) >= 2:
            sorted_dates = data.index.sort_values()
            current_date = sorted_dates[-1]
            previous_date = sorted_dates[-2]
            previous_close = data.loc[previous_date, "Close"]
            current_close = data.loc[current_date, "Close"]
            if previous_close == 0:
                return None
            percent = (current_close - previous_close) / previous_close * 100
            return percent
        else:
            return None
    except:
        return None

def add_fibonacci_lines(fig, high, low):
    levels = [0.0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0]
    colors = ["#ffe6e6", "#ffcccc", "#ff9999", "#ff6666", "#ff3333", "#cc0000", "#990000"]
    for level, color in zip(levels, colors):
        price = high - (high - low) * level
        fig.add_hline(
            y=price,
            line_dash="dot",
            line_color=color,
            annotation_text=f"{level:.3f}",
            annotation_position="top right"
        )
    return fig

def render():
    st.header("📊 매크로지표")

    vix = fetch_price("^VIX")
    irx = fetch_price("^IRX")
    tnx = fetch_price("^TNX")
    tyx = fetch_price("^TYX")
    sp500 = fetch_price("^GSPC")
    dji = fetch_price("^DJI")
    nasdaq = fetch_price("^IXIC")
    usd_idx = fetch_price("DX-Y.NYB")
    gold = fetch_price("GC=F")
    oil = fetch_price("CL=F")
    copper = fetch_price("HG=F")  # 구리 선물

    spread_10y_3m  = tnx - irx if tnx and irx else None
    spread_30y_10y = tyx - tnx if tyx and tnx else None

    indicators = [
        {"name": "VIX", "ticker": "^VIX", "value": vix},
        {"name": "S&P 500", "ticker": "^GSPC", "value": sp500},
        {"name": "다우존스", "ticker": "^DJI", "value": dji},
        {"name": "나스닥", "ticker": "^IXIC", "value": nasdaq},
        {"name": "달러지수", "ticker": "DX-Y.NYB", "value": usd_idx},
        {"name": "금", "ticker": "GC=F", "value": gold},
        {"name": "원유", "ticker": "CL=F", "value": oil},
        {"name": "구리", "ticker": "HG=F", "value": copper},
        {"name": "10년 수익률", "ticker": "^TNX", "value": tnx},
        {"name": "30년 수익률", "ticker": "^TYX", "value": tyx},
        {"name": "3개월 수익률", "ticker": "^IRX", "value": irx},
    ]
    if spread_10y_3m is not None:
        indicators.append({"name": "10년-3개월 차이", "ticker": "spread_10y_3m", "value": spread_10y_3m})
    if spread_30y_10y is not None:
        indicators.append({"name": "30년-10년 차이", "ticker": "spread_30y_10y", "value": spread_30y_10y})

    chart_indicators = [i for i in indicators if not i["ticker"].startswith("spread")]
    for ind in chart_indicators:
        ind["change"] = get_change(ind["ticker"])

    tabs = st.tabs(["대시보드"] + [i["name"] for i in chart_indicators])

    with tabs[0]:
        card_css = """
        <style>
          .dashboard {
              display: grid;
              grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
              gap: 1rem;
          }
          .card {
              border-radius: 12px;
              padding: 1.2rem;
              box-shadow: 2px 4px 10px rgba(0,0,0,0.1);
              color: #fff;
              text-align: center;
              font-family: 'Segoe UI', sans-serif;
              transition: transform 0.2s;
              background: rgba(255, 255, 255, 0.1);
              backdrop-filter: blur(6px);
          }
          .card:hover {
              transform: scale(1.02);
          }
          .card.positive {
              background: linear-gradient(135deg, #0f9d58, #34a853);
          }
          .card.negative {
              background: linear-gradient(135deg, #d93025, #ea4335);
          }
          .card.neutral {
              background: linear-gradient(135deg, #888, #aaa);
          }
          .card-title {
              font-size: 1.1rem;
              margin-bottom: 0.5rem;
          }
          .card-value {
              font-size: 1.8rem;
              font-weight: bold;
              margin-bottom: 0.3rem;
          }
          .card-change {
              font-size: 1.2rem;
          }
        </style>
        """
        cards_html = "<div class='dashboard'>"
        for ind in chart_indicators:
            val = ind.get("value")
            display_val = f"{val:.2f}" if isinstance(val, (int, float)) else "N/A"
            change = ind.get("change")
            if isinstance(change, float):
                display_change = f"{change:+.2f}%"
                card_class = "positive" if change >= 0 else "negative"
            else:
                display_change = "N/A"
                card_class = "neutral"
            card_html = f"""
            <div class="card {card_class}">
              <div class="card-title">{ind['name']}</div>
              <div class="card-value">{display_val}</div>
              <div class="card-change">{display_change}</div>
            </div>
            """
            cards_html += card_html
        cards_html += "</div>"

        html_content = card_css + cards_html
        components.html(html_content, height=600, scrolling=True)

    for ind, tab in zip(chart_indicators, tabs[1:]):
        with tab:
            st.header(f"{ind['name']} 차트 (1년)")
            try:
                data = yf.Ticker(ind["ticker"]).history(period="1y")
                if not data.empty:
                    close = data["Close"]
                    fig = px.line(data, x=data.index, y="Close", title=ind["name"])
                    fig.update_layout(
                        yaxis_range=[close.min() * 0.95, close.max() * 1.05],
                        height=500
                    )
                    if ind["ticker"] == "^VIX":
                        for level in [15, 20, 25, 30]:
                            fig.add_hline(y=level, line_dash="dash", annotation_text=str(level))
                    if ind["ticker"] in ["^GSPC", "^IXIC", "^DJI"]:
                        fig = add_fibonacci_lines(fig, close.max(), close.min())
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("데이터가 없습니다.")
            except Exception as e:
                st.error(f"오류 발생: {e}")