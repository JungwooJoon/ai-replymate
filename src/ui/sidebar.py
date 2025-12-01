import streamlit as st
import time  # 딜레이 효과용
from src.ui.styles import apply_custom_style
from src.data_manager import reset_app_data
from src.rag import ReplyMateRAG


def render_sidebar():
    apply_custom_style()

    with st.sidebar:
        st.header("AI ReplyMate")
        st.markdown("---")
        st.subheader("⚙️ 설정 (Settings)")
        tone = st.selectbox(
            "🗣️ 답글 톤 설정",
            ["정중한", "친근한", "유머러스한", "사장님 말투"],
            index=0
        )
        st.info(f"현재 모드: **{tone}**")

        st.markdown("<br>" * 3, unsafe_allow_html=True)

        # ---------------------------------------------------------
        # [NEW] 개발자용 리셋 기능 (Expander로 숨김 처리)
        # ---------------------------------------------------------
        with st.expander("🔧 개발자 도구 (Reset)", expanded=False):
            st.caption("모든 학습 데이터와 저장된 리뷰를 삭제하고 초기 상태로 되돌립니다.")

            # 버튼 클릭 시 동작
            if st.button("🚨 시스템 전체 초기화", type="primary", width='stretch'):
                with st.spinner("시스템 초기화 중..."):
                    # 1. JSON 데이터 원복
                    reset_app_data()

                    # 2. ChromaDB 재구축
                    rag = ReplyMateRAG()
                    rag.init_db()

                    # 3. 세션 상태 초기화 (메모리 비우기)
                    for key in list(st.session_state.keys()):
                        del st.session_state[key]

                    time.sleep(1)  # 사용자 확인용 딜레이

                st.success("초기화 완료! 앱을 재실행합니다.")
                time.sleep(1)
                st.rerun()  # 앱 새로고침

        st.markdown("<br>", unsafe_allow_html=True)
        st.caption("Developed by Gemini")
        return tone