import streamlit as st
import time
from src.ui.styles import apply_custom_style
from src.data_manager import reset_app_data, save_store_name, load_store_name
from src.rag import ReplyMateRAG


def render_sidebar():
    apply_custom_style()

    with st.sidebar:
        st.header("AI ReplyMate")
        st.markdown("---")

        # ---------------------------------------------------------
        # [NEW] 가게 이름 설정 (전역 설정)
        # ---------------------------------------------------------
        st.subheader("가게 설정")

        if "store_name" not in st.session_state:
            st.session_state.store_name = load_store_name()

        store_name = st.text_input(
            "가게 이름 (상호명)",
            value=st.session_state.store_name,
            placeholder="예: 맛있는 떡볶이",
            key="input_store_name"
        )

        # 변경 시 자동 저장
        if store_name != st.session_state.store_name:
            st.session_state.store_name = store_name
            save_store_name(store_name)
            st.toast(f"가게 이름 저장됨: {store_name}", icon=":material/save:")

        st.markdown("---")

        st.subheader("⚙️ 답글 설정")
        tone = st.selectbox(
            "답글 톤 설정",
            ["정중한", "친근한", "유머러스한", "사장님 말투"],
            index=0
        )
        st.info(f"현재 모드: **{tone}**")

        st.markdown("<br>" * 3, unsafe_allow_html=True)

        with st.expander("🔧 개발자 도구", expanded=False):
            st.caption("모든 데이터 초기화")
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

        # [RETURN] 톤과 가게 이름 반환
        return tone, store_name