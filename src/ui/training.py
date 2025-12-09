import streamlit as st
import pandas as pd
from src.models import auto_classify_reply
from src.data_manager import load_json_data, save_json_data
from src.rag import ReplyMateRAG


def render_training_tab():
    st.markdown("### :material/record_voice_over: 사장님 말투 학습")

    # --------------------------------------------------------------------------
    # 1. 말투 추가 (입력 폼)
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
    # 2. 학습 내역 관리 (수정/삭제 기능 추가)
    # --------------------------------------------------------------------------
    st.markdown("#### :material/edit: 학습 내역 관리")
    st.caption("이미 학습된 말투를 수정하거나 삭제할 수 있습니다.")

    # 전체 데이터 로드
    all_templates = load_json_data("templates.json")

    # 'owner_custom' 데이터만 필터링
    owner_data = [t for t in all_templates if t.get("metadata", {}).get("tone") == "owner_custom"]

    if owner_data:
        # 데이터프레임으로 변환 (편집용)
        # content와 metadata 내부의 sentiment, category를 분리해서 표시
        display_data = []
        for t in owner_data:
            display_data.append({
                "content": t["content"],
                "sentiment": t["metadata"].get("sentiment", "positive"),
                "category": t["metadata"].get("category", "service")
            })

        df = pd.DataFrame(display_data)

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

                    # 3. 합치기 (보존된 데이터 + 수정된 사장님 데이터)
                    final_data = other_data + updated_owner_data

                    # 4. 파일 저장
                    save_json_data("templates.json", final_data)

                    # 5. DB 재구축 (필수)
                    rag = ReplyMateRAG()
                    rag.init_db()

                st.success("학습 내역이 수정되었습니다!")
                st.rerun()
    else:
        st.info("아직 학습된 데이터가 없습니다. 위에서 입력하여 추가해보세요.")