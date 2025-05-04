import streamlit as st

# ✅ 무조건 가장 먼저!
st.set_page_config(
    page_title="Market App",
    layout="wide",
    initial_sidebar_state="collapsed"
)

import os, sys
import importlib
from urllib.parse import unquote
from components.nav import render_nav  # Assuming this module exists


# Hide default sidebar elements
st.markdown(
    """
    <style>
        [data-testid="stSidebar"],
        [data-testid="stSidebarNav"],
        [data-testid="collapsedControl"] {
            display: none;
        }
    </style>
    """,
    unsafe_allow_html=True
)
st.markdown(
    """
    <style>
        [data-testid="stSidebarCollapsedControl"] {
            display: none !important;
        }
    </style>
    """,
    unsafe_allow_html=True
)
st.markdown(
    """
    <style>
        .block-container {
            padding-top: 1rem !important;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# Determine the current page from the query parameters
query_params = st.query_params
current_page = query_params.get("page", "dashboard")
current_page = unquote(current_page)

# Render navigation bar (vertical layout)
with st.container():
    render_nav(current_page, direction="vertical")

# Dynamically load and render the desired page
if current_page == "dashboard":
    import pages.dashboard as dashboard
    importlib.reload(dashboard)
    dashboard.render()
elif current_page == "dividends":
    import pages.dividends as dividends
    importlib.reload(dividends)
    dividends.render()
elif current_page == "etfs":
    import pages.etfs as etfs
    importlib.reload(etfs)
    etfs.render()
elif current_page == "stocks":
    import pages.stocks as stocks
    importlib.reload(stocks)
    stocks.render()
elif current_page == "stock_calc":
    import pages.stock_calc as stock_calc
    importlib.reload(stock_calc)
    stock_calc.render()
elif current_page == "favorite_stocks":
    import pages.favorite_stocks as favorite_stocks
    importlib.reload(favorite_stocks)
    favorite_stocks.render()
elif current_page == "my_dividend_report":
    import pages.my_dividend_report as my_dividend_report
    importlib.reload(my_dividend_report)
    my_dividend_report.render_page()
else:
    st.error("Page not found.")