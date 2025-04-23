import yfinance as yf
import pandas as pd

def analyze_etf(ticker="SCHD"):
    ticker_obj = yf.Ticker(ticker)

    # 종목 정보
    info = ticker_obj.info
    short_name = info.get("shortName", ticker)
    sector = info.get("sector", "N/A")
    dividend_yield = info.get("dividendYield")
    payout_ratio = info.get("payoutRatio")
    price_to_book = info.get("priceToBook")
    beta = info.get("beta")
    trailing_pe = info.get("trailingPE")

    # 가격 데이터 (3년치)
    data = ticker_obj.history(period="3y")
    if data.empty:
        print("⚠️ 가격 데이터를 가져올 수 없습니다.")
        return
    close = data["Close"]
    current_price = close.iloc[-1]

    # 배당금 데이터
    dividends = ticker_obj.dividends
    if dividends.empty:
        print("⚠️ 배당 데이터를 가져올 수 없습니다.")
        return
    last_1y_dividends = dividends[dividends.index > (dividends.index.max() - pd.DateOffset(years=1))]
    div_sum_1y = last_1y_dividends.sum()

    # 배당 수익률 (직접 계산)
    div_yield_calc = (div_sum_1y / current_price) * 100 if current_price else None

    # 수익률 및 변동성
    returns = close.pct_change().dropna()
    mean_return = returns.mean() * 100
    std_return = returns.std() * 100
    sharpe_ratio = (mean_return - 0.1) / std_return if std_return else None  # 무위험 수익률 0.1%

    # 출력
    print(f"📌 종목: {ticker} ({short_name})")
    print(f"현재 주가: ${current_price:.2f}")
    print(f"최근 1년 배당 총액: ${div_sum_1y:.4f}")
    print(f"시가 배당률 (계산): {div_yield_calc:.2f}%" if div_yield_calc else "배당 수익률: N/A")
    print(f"평균 일수익률: {mean_return:.3f}%")
    print(f"수익률 표준편차: {std_return:.3f}%")
    print(f"Sharpe Ratio: {sharpe_ratio:.3f}" if sharpe_ratio else "Sharpe Ratio: N/A")
    print(f"섹터: {sector}")

    # 추가 보조지표
    print("\n📊 추가 펀더멘털 지표")
    print(f"배당 수익률 (yfinance): {dividend_yield * 100:.2f}%" if dividend_yield else "배당 수익률 (yfinance): N/A")
    print(f"배당성향 (Payout Ratio): {payout_ratio:.2f}" if payout_ratio else "배당성향: N/A")
    print(f"P/B (주가순자산비율): {price_to_book:.2f}" if price_to_book else "P/B: N/A")
    print(f"Beta (변동성 지표): {beta:.2f}" if beta else "Beta: N/A")
    print(f"PER (Trailing P/E): {trailing_pe:.2f}" if trailing_pe else "PER: N/A")

if __name__ == "__main__":
    analyze_etf("TSLA")
