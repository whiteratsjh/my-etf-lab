import os
import datetime

# 기본 데이터 디렉토리
BASE_DIR = os.path.join("E:\\project\\my-etf-lab", "data")

# 세부 경로 설정
DATA_DIR = BASE_DIR
STOCK_DATA_DIR = os.path.join(DATA_DIR, "stock_data")
STOCK_INSIGHT_DIR = os.path.join(DATA_DIR, "stock_insight")
FAVORITE_FILE = os.path.join(DATA_DIR, "favorite.json")

# 파일 유효기간 (예: 7일)
FILE_EXPIRY_DAYS = 7

# 오늘 날짜 문자열
TODAY_STR = datetime.datetime.today().strftime("%Y%m%d")
