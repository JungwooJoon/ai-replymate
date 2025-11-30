import streamlit as st
import pandas as pd
from src.data_manager import load_json_data, save_json_data
from src.rag import ReplyMateRAG


def render_menu_tab():
    st.markdown("### 🍽️ 메뉴 정보 관리")

    with st.container(border=True):
        st.caption("AI가 답글 작성 시 참고할 메뉴 정보를 입력하세요. 특징을 자세히 적을수록 AI가 더 구체적인 답변을 합니다.")

        # 1. 데이터 로드
        menu_data = load_json_data("menu_info.json")

        # 데이터프레임 변환
        if menu_data:
            df = pd.DataFrame(menu_data)
        else:
            # 데이터가 없을 경우 기본 템플릿 제공
            df = pd.DataFrame(columns=["menu_name", "description", "category"])

        # 2. 데이터 에디터 (엑셀처럼 수정 가능)
        edited_df = st.data_editor(
            df,
            num_rows="dynamic",  # 행 추가/삭제 허용
            width='stretch',
            column_config={
                "menu_name": st.column_config.TextColumn(
                    "메뉴명",
                    help="예: 치즈돈까스",
                    required=True
                ),
                "description": st.column_config.TextColumn(
                    "메뉴 특징/조리법 (AI 참고용)",
                    help="예: 100% 모짜렐라 치즈 사용, 전자레인지 30초 권장",
                    width="large",
                    required=True
                ),
                "category": st.column_config.SelectboxColumn(
                    "카테고리",
                    help="메뉴의 종류",
                    options=["main", "side", "drink", "dessert", "set"],
                    required=True
                )
            },
            hide_index=True,
            key="menu_editor"
        )

        st.markdown("<div style='margin: 10px 0;'></div>", unsafe_allow_html=True)

        # 3. 저장 버튼
        col1, col2 = st.columns([4, 1])
        with col2:
            if st.button("저장 및 AI 학습 💾", type="primary", width='stretch'):
                if not edited_df.empty:
                    with st.spinner("메뉴 정보를 저장하고 AI를 다시 학습시키는 중..."):
                        # DataFrame -> List of Dict 변환
                        updated_data = edited_df.to_dict(orient="records")

                        # JSON 저장
                        save_json_data("menu_info.json", updated_data)

                        # [중요] RAG DB 업데이트 (그래야 AI가 알 수 있음)
                        rag = ReplyMateRAG()
                        rag.init_db()

                    st.success("메뉴 정보가 업데이트되었습니다!")
                else:
                    st.warning("저장할 메뉴 데이터가 없습니다.")

    # 팁 섹션
    st.markdown("---")
    with st.expander("💡 메뉴 설명(Description) 작성 팁"):
        st.markdown("""
        AI는 **'메뉴 특징'**에 적힌 내용을 바탕으로 답글을 씁니다.

        * **좋은 예:** `100% 모짜렐라 치즈, 식으면 전자레인지 30초 돌려주세요.` -> AI가 "식었으면 데워 드세요"라고 안내 가능.
        * **나쁜 예:** `맛있음.` -> AI가 할 말이 없음.
        * **추천 내용:** 재료 원산지, 맛있게 먹는 법, 조리 특징, 포장 용기 특징 등.
        """)