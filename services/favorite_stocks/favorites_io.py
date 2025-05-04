import json
import os
import streamlit as st
from utils.constants import FAVORITE_FILE

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
