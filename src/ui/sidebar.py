import streamlit as st
import time
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
            "답글 톤 설정",  # 이모티콘 제거
            ["정중한", "친근한", "유머러스한", "사장님 말투"],
            index=0
        )
        st.info(f"현재 모드: **{tone}**")

        st.markdown("<br>" * 3, unsafe_allow_html=True)

        with st.expander("🔧 개발자 도구", expanded=False):
            st.caption("모든 데이터 초기화")
            # [ICON] 경고 아이콘
            if st.button("시스템 전체 초기화", icon=":material/warning:", type="primary", width='stretch'):
                with st.spinner("초기화 중..."):
                    reset_app_data()
                    rag = ReplyMateRAG()
                    rag.init_db()
                    for key in list(st.session_state.keys()):
                        del st.session_state[key]
                    time.sleep(1)
                st.success("완료!")
                time.sleep(0.5)
                st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        st.caption("Developed by Gemini")
        return tone