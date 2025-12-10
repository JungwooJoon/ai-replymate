import streamlit as st
import pandas as pd
import io
from src.models import auto_classify_reply
from src.data_manager import load_json_data, save_json_data
from src.rag import ReplyMateRAG


def render_training_tab():
    st.markdown("### :material/record_voice_over: 사장님 말투 학습")

    # --------------------------------------------------------------------------
    # 1. 말투 추가 (기본 입력 폼)
    # --------------------------------------------------------------------------
    with st.container(border=True):
        st.caption("평소 말투를 입력하면 AI가 학습합니다.")
        with st.form("simple_training_form"):
            owner_reply = st.text_area(
                "답글 예시 입력",
                placeholder="예: 아이고 고객님~ 또 오세유!",
                height=100
            )

            if st.form_submit_button("학습 시작", icon=":material/school:"):
                if owner_reply:
                    with st.spinner("분석 중..."):
                        # AI가 메타데이터(감정/카테고리) 자동 분석
                        meta = auto_classify_reply(owner_reply)

                        new_entry = {
                            "content": owner_reply,
                            "metadata": {
                                "sentiment": meta.get("sentiment", "positive"),
                                "category": meta.get("category", "service"),
                                "tone": "owner_custom"
                            }
                        }

                        templates = load_json_data("templates.json")
                        templates.append(new_entry)
                        save_json_data("templates.json", templates)

                        # RAG DB 업데이트
                        rag = ReplyMateRAG()
                        rag.init_db()

                        st.success(f"학습 완료! ({meta['sentiment']})")
                        st.rerun()
                else:
                    st.warning("내용 입력 필요")

    st.markdown("---")

    # --------------------------------------------------------------------------
    # 2. [NEW] 엑셀/CSV 일괄 업로드 섹션
    # --------------------------------------------------------------------------
    with st.expander("📂 엑셀/CSV로 말투 일괄 업로드하기", icon=":material/upload_file:"):
        st.caption("여러 말투 데이터를 한 번에 등록하려면 엑셀이나 CSV 파일을 업로드하세요.")

        c_down, c_up = st.columns([1, 2])

        # 1) 양식 다운로드 버튼
        with c_down:
            # 예시 데이터 생성
            sample_data = pd.DataFrame([
                {"content": "아이고 고객님~ 맛있게 드셨다니 다행이네유!", "sentiment": "positive", "category": "taste_good"},
                {"content": "죄송해유ㅠㅠ 다음엔 더 신경쓸게유...", "sentiment": "negative", "category": "service"}
            ])

            # CSV 변환
            csv_buffer = io.StringIO()
            sample_data.to_csv(csv_buffer, index=False, encoding="utf-8-sig")

            st.download_button(
                label="양식 다운로드",
                data=csv_buffer.getvalue(),
                file_name="말투학습_양식.csv",
                mime="text/csv",
                icon=":material/download:",
                width='stretch'
            )

        # 2) 파일 업로드
        with c_up:
            uploaded_file = st.file_uploader("파일 선택 (xlsx, csv)", type=["xlsx", "csv"], label_visibility="collapsed",
                                             key="tone_uploader")

            new_uploaded_df = None
            if uploaded_file is not None:
                try:
                    # 파일 읽기
                    if uploaded_file.name.endswith('.csv'):
                        new_uploaded_df = pd.read_csv(uploaded_file)
                    else:
                        new_uploaded_df = pd.read_excel(uploaded_file)

                    # 컬럼 확인 (유효성 검사)
                    required_cols = {'content', 'sentiment', 'category'}
                    if not required_cols.issubset(new_uploaded_df.columns):
                        st.error(f"파일 형식이 올바르지 않습니다. 필수 컬럼: {required_cols}")
                        new_uploaded_df = None
                    else:
                        st.toast(f"{len(new_uploaded_df)}개의 말투 데이터를 불러왔습니다. 아래 표에서 확인 후 '수정사항 저장'을 눌러주세요.",
                                 icon=":material/check:")

                except Exception as e:
                    st.error(f"파일을 읽는 중 오류가 발생했습니다: {e}")

    # --------------------------------------------------------------------------
    # 3. 학습 내역 관리 (에디터)
    # --------------------------------------------------------------------------
    st.markdown("#### :material/edit: 학습 내역 관리")

    # 전체 데이터 로드
    all_templates = load_json_data("templates.json")

    # 'owner_custom' 데이터만 필터링
    owner_data = [t for t in all_templates if t.get("metadata", {}).get("tone") == "owner_custom"]

    # 표시할 데이터 구성
    display_data = []
    for t in owner_data:
        display_data.append({
            "content": t["content"],
            "sentiment": t["metadata"].get("sentiment", "positive"),
            "category": t["metadata"].get("category", "service")
        })

    df = pd.DataFrame(display_data)

    # [NEW] 업로드된 데이터가 있다면 병합해서 미리보기에 추가
    if new_uploaded_df is not None:
        df = pd.concat([df, new_uploaded_df], ignore_index=True)

    if not df.empty:
        # 데이터 에디터 표시
        edited_df = st.data_editor(
            df,
            num_rows="dynamic",  # 행 추가/삭제 가능
            width='stretch',
            column_config={
                "content": st.column_config.TextColumn("말투 예시 (내용)", width="large", required=True),
                "sentiment": st.column_config.SelectboxColumn(
                    "감정",
                    options=["positive", "negative"],
                    width="small",
                    required=True
                ),
                "category": st.column_config.SelectboxColumn(
                    "카테고리",
                    options=["taste_good", "taste_bad", "delivery_delay", "wrong_item", "quantity", "service"],
                    width="medium",
                    required=True
                )
            },
            key="training_editor"
        )

        st.markdown("<div style='margin-bottom: 10px;'></div>", unsafe_allow_html=True)

        # [저장 버튼] 변경사항 반영
        col1, col2 = st.columns([4, 1])
        with col2:
            if st.button("수정사항 저장", icon=":material/save:", type="primary", width='stretch'):
                with st.spinner("데이터 업데이트 중..."):
                    # 1. 에디터의 내용을 딕셔너리 리스트로 변환
                    updated_owner_data = []
                    for _, row in edited_df.iterrows():
                        updated_owner_data.append({
                            "content": row["content"],
                            "metadata": {
                                "sentiment": row["sentiment"],
                                "category": row["category"],
                                "tone": "owner_custom"  # 톤은 고정
                            }
                        })

                    # 2. 기존 전체 데이터에서 'owner_custom'이 아닌 것만 남김 (보존)
                    other_data = [t for t in all_templates if t.get("metadata", {}).get("tone") != "owner_custom"]

                    # 3. 합치기
                    final_data = other_data + updated_owner_data

                    # 4. 파일 저장
                    save_json_data("templates.json", final_data)

                    # 5. DB 재구축 (필수)
                    rag = ReplyMateRAG()
                    rag.init_db()

                st.success("학습 내역이 저장되었습니다!")
                st.rerun()
    else:
        st.info("학습된 데이터가 없습니다. 직접 입력하거나 엑셀 파일을 업로드하세요.")