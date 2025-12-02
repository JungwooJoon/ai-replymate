import streamlit as st
import pandas as pd
from src.data_manager import load_json_data, save_json_data
from src.rag import ReplyMateRAG


def render_menu_tab():
    # [ICON]
    st.markdown("### :material/restaurant_menu: 메뉴 정보 관리")

    with st.container(border=True):
        st.caption("AI가 참고할 메뉴 정보를 입력하세요.")

        menu_data = load_json_data("menu_info.json")

        if menu_data:
            df = pd.DataFrame(menu_data)
        else:
            df = pd.DataFrame(columns=["menu_name", "description", "category"])

        edited_df = st.data_editor(
            df,
            num_rows="dynamic",
            width='stretch',
            column_config={
                "menu_name": st.column_config.TextColumn("메뉴명", required=True),
                "description": st.column_config.TextColumn("특징/조리법", width="large", required=True),
                "category": st.column_config.SelectboxColumn(
                    "카테고리",
                    options=["main", "side", "drink", "dessert", "set"],
                    required=True
                )
            },
            hide_index=True,
            key="menu_editor"
        )

        st.markdown("<div style='margin: 10px 0;'></div>", unsafe_allow_html=True)

        col1, col2 = st.columns([4, 1])
        with col2:
            # [ICON] 저장
            if st.button("저장 및 학습", icon=":material/save:", type="primary", width='stretch'):
                if not edited_df.empty:
                    with st.spinner("AI 학습 중..."):
                        updated_data = edited_df.to_dict(orient="records")
                        save_json_data("menu_info.json", updated_data)
                        rag = ReplyMateRAG()
                        rag.init_db()
                    st.success("완료!")
                else:
                    st.warning("데이터 없음")

    st.markdown("---")
    # [ICON] 팁
    with st.expander("도움말", icon=":material/lightbulb:"):
        st.markdown("""
        AI는 **'특징/조리법'**을 바탕으로 답글을 씁니다.
        * **Good:** `100% 모짜렐라, 전자레인지 30초`
        * **Bad:** `맛있음`
        """)