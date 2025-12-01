import streamlit as st
from src.utils import load_config, get_page_config
from src.ui.sidebar import render_sidebar
from src.ui.cards import render_review_cards_tab
from src.ui.dashboard import render_dashboard_tab
from src.ui.training import render_training_tab
from src.ui.menu import render_menu_tab
import sys

try:
    import pysqlite3
    sys.modules['sqlite3'] = pysqlite3
except ImportError:
    pass

# 초기 설정
st.set_page_config(**get_page_config())
load_config()


def main():
    st.title("💬 AI ReplyMate")

    # 사이드바 (톤 설정)
    selected_tone = render_sidebar()

    # 탭 구성
    tab1, tab2, tab3, tab4 = st.tabs(["✨ 리뷰 관리", "📊 대시보드", "🍽️ 메뉴 관리", "🗣️ 말투 학습"])

    with tab1:
        # [Req 2] 카드형 UI
        render_review_cards_tab(selected_tone)

    with tab2:
        # [Req 3] 완료된 데이터 대시보드
        render_dashboard_tab()
    with tab3:
        # [NEW] 메뉴 관리 화면 렌더링
        render_menu_tab()

    with tab4:
        # [Req 4] 간편 말투 학습
        render_training_tab()


if __name__ == "__main__":
    main()