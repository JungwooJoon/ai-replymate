import os
import sys

try:
    # pysqlite3를 시스템의 기본 sqlite3로 강제 교체 (배포용 패치)
    __import__('pysqlite3')
    import sys

    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except (ImportError, KeyError):
    pass

import streamlit as st
from src.utils import load_config, get_page_config

# 분할된 UI 모듈 임포트
from src.ui.sidebar import render_sidebar
from src.ui.cards import render_review_cards_tab
from src.ui.dashboard import render_dashboard_tab
from src.ui.training import render_training_tab
from src.ui.menu import render_menu_tab

# 초기 설정
st.set_page_config(**get_page_config())
load_config()


def main():
    # [ICON] 타이틀 아이콘 변경
    st.title(":material/forum: AI ReplyMate")

    # 사이드바 렌더링
    selected_tone = render_sidebar()

    # 탭 구성 (이모티콘 -> 아이콘 변경)
    tab1, tab2, tab3, tab4 = st.tabs([
        ":material/rate_review: 리뷰 관리",
        ":material/bar_chart: 대시보드",
        ":material/restaurant_menu: 메뉴 관리",
        ":material/record_voice_over: 말투 학습"
    ])

    with tab1:
        render_review_cards_tab(selected_tone)

    with tab2:
        render_dashboard_tab()

    with tab3:
        render_menu_tab()

    with tab4:
        render_training_tab()


if __name__ == "__main__":
    main()