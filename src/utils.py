import os
import streamlit as st
from dotenv import load_dotenv


def load_config():
    """환경 변수 로드 및 기본 설정"""
    load_dotenv()

    # API 키 확인
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        st.error("[CRITICAL] GOOGLE_API_KEY가 .env 파일에 설정되지 않았습니다.")
        st.stop()
    return True


def get_page_config():
    """Streamlit 페이지 설정 반환"""
    return {
        "page_title": "AI ReplyMate",
        "page_icon": "💬",
        "layout": "wide",
        "initial_sidebar_state": "expanded"
    }


def clear_generated_state():
    """새로운 리뷰 입력 시 기존 생성 결과 초기화"""
    if "generated_reply" in st.session_state:
        st.session_state.generated_reply = None
    if "last_review" in st.session_state:
        st.session_state.last_review = None