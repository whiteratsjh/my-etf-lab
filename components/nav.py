import streamlit as st


def render_nav(active_page: str, direction: str = "horizontal"):
    nav_style = """
        <style>
            .nav-container {
                display: flex;
                flex-direction: DIRECTION;
                gap: 1rem;
                background-color: #f0f2f6;
                padding: 1rem;
                border-radius: 0.5rem;
                margin-bottom: 2rem;
            }
            .nav-link {
                font-size: 1rem;
                font-weight: 600;
                color: #555;
                text-decoration: none;
                padding: 0.5rem 1rem;
                border-radius: 8px;
            }
            .nav-link:hover {
                background-color: #e3e8f0;
            }
            .nav-link.active {
                background-color: #0066cc;
                color: white;
            }
        </style>
    """.replace("DIRECTION", "row")  # 항상 가로로 배치

    st.markdown(nav_style, unsafe_allow_html=True)

    pages = {
        "dashboard": "📊 매크로지표",
        "dividends": "📈 배당 정보",
        "etfs": "📘 ETF 분석",
        "stocks": "🟧 개별 종목 분석",
        "stock_calc": "🧮 매수 계산기",
        "favorite_stocks": "⭐ 관심종목"
    }


    links_html = "".join([
        f'<a class="nav-link {"active" if page == active_page else ""}" href="?page={page}">{label}</a>'
        for page, label in pages.items()
    ])
    st.html(f"<div class='nav-container'>{links_html}</div>")
