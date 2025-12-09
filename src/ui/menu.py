import streamlit as st
import pandas as pd
import io
from src.data_manager import load_json_data, save_json_data
from src.rag import ReplyMateRAG


def render_menu_tab():
    st.markdown("### :material/restaurant_menu: 메뉴 정보 관리")

    # 1. 데이터 로드 (기본)
    menu_data = load_json_data("menu_info.json")
    if menu_data:
        df = pd.DataFrame(menu_data)
    else:
        df = pd.DataFrame(columns=["menu_name", "description", "category"])

    # ==========================================================================
    # [NEW] 엑셀/CSV 일괄 업로드 섹션
    # ==========================================================================
    with st.expander("📂 엑셀/CSV로 일괄 업로드하기", icon=":material/upload_file:"):
        st.caption("많은 메뉴를 한 번에 등록하려면 엑셀이나 CSV 파일을 업로드하세요.")

        c_down, c_up = st.columns([1, 2])

        # 1) 양식 다운로드 버튼
        with c_down:
            # 예시 데이터 생성
            sample_data = pd.DataFrame([
                {"menu_name": "예시_치즈돈까스", "description": "100% 모짜렐라, 전자레인지 30초", "category": "main"},
                {"menu_name": "예시_콜라", "description": "코카콜라 500ml", "category": "drink"}
            ])

            # CSV 변환
            csv_buffer = io.StringIO()
            sample_data.to_csv(csv_buffer, index=False, encoding="utf-8-sig")

            st.download_button(
                label="양식 다운로드",
                data=csv_buffer.getvalue(),
                file_name="메뉴등록_양식.csv",
                mime="text/csv",
                icon=":material/download:",
                width='stretch'
            )

        # 2) 파일 업로드
        with c_up:
            uploaded_file = st.file_uploader("파일 선택 (xlsx, csv)", type=["xlsx", "csv"], label_visibility="collapsed")

            if uploaded_file is not None:
                try:
                    # 파일 읽기
                    if uploaded_file.name.endswith('.csv'):
                        new_data = pd.read_csv(uploaded_file)
                    else:
                        new_data = pd.read_excel(uploaded_file)

                    # 컬럼 확인 (유효성 검사)
                    required_cols = {'menu_name', 'description', 'category'}
                    if not required_cols.issubset(new_data.columns):
                        st.error(f"파일 형식이 올바르지 않습니다. 필수 컬럼: {required_cols}")
                    else:
                        # 기존 데이터와 병합 (화면에만 반영, 저장은 버튼 눌러야 함)
                        # 필요한 컬럼만 추출
                        new_data = new_data[["menu_name", "description", "category"]]
                        df = pd.concat([df, new_data], ignore_index=True)
                        st.toast(f"{len(new_data)}개의 메뉴를 불러왔습니다. 아래에서 확인 후 '저장'을 눌러주세요.", icon=":material/check:")

                except Exception as e:
                    st.error(f"파일을 읽는 중 오류가 발생했습니다: {e}")

    # ==========================================================================
    # [EXISTING] 데이터 에디터 및 저장
    # ==========================================================================

    with st.container(border=True):
        st.info("아래 표에서 내용을 수정하거나 추가할 수 있습니다.")

        # 데이터 에디터 (업로드된 내용이 있다면 df에 합쳐져서 보임)
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
            if st.button("저장 및 학습", icon=":material/save:", type="primary", width='stretch'):
                if not edited_df.empty:
                    with st.spinner("AI 학습 중..."):
                        # 최종 데이터를 JSON으로 저장
                        updated_data = edited_df.to_dict(orient="records")
                        save_json_data("menu_info.json", updated_data)

                        # RAG 업데이트
                        rag = ReplyMateRAG()
                        rag.init_db()
                    st.success("메뉴 정보가 저장되었습니다!")
                else:
                    st.warning("저장할 데이터가 없습니다.")

    st.markdown("---")
    with st.expander("도움말", icon=":material/lightbulb:"):
        st.markdown("""
        AI는 **'특징/조리법'**을 바탕으로 답글을 씁니다.
        * **엑셀 업로드:** [양식 다운로드] 후 내용을 채워서 업로드하면 자동으로 표에 추가됩니다.
        * **Good:** `100% 모짜렐라, 전자레인지 30초`
        * **Bad:** `맛있음`
        """)