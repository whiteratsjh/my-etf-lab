import os
import pandas as pd
import datetime
import yfinance as yf
import logging

from utils.constants import STOCK_DATA_DIR, TODAY_STR, FILE_EXPIRY_DAYS

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s:%(message)s")

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

def get_stock_data(ticker):
    cleanup_old_files(STOCK_DATA_DIR)
    file_path = os.path.join(STOCK_DATA_DIR, f"{ticker}_{TODAY_STR}.csv")
    
    if os.path.exists(file_path):
        df = pd.read_csv(file_path, index_col="Date", parse_dates=True)
        logging.info(f"Using cached data for {ticker} from {file_path}")
    else:
        ticker_obj = yf.Ticker(ticker)
        df = ticker_obj.history(period="3y")
        if df.empty:
            return None
        df.to_csv(file_path)
        logging.info(f"Saved new data for {ticker} to {file_path}")
    
    return df
