import streamlit as st
from src.models import auto_classify_reply
from src.data_manager import load_json_data, save_json_data
from src.rag import ReplyMateRAG


def render_training_tab():
    # [ICON]
    st.markdown("### :material/record_voice_over: 사장님 말투 학습")

    with st.container(border=True):
        st.caption("평소 말투를 입력하면 AI가 학습합니다.")
        with st.form("simple_training_form"):
            owner_reply = st.text_area(
                "답글 예시 입력",
                placeholder="예: 아이고 고객님~ 또 오세유!",
                height=100
            )

            # [ICON] 학습
            if st.form_submit_button("학습 시작", icon=":material/school:"):
                if owner_reply:
                    with st.spinner("분석 중..."):
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

                        rag = ReplyMateRAG()
                        rag.init_db()

                        st.success(f"학습 완료! ({meta['sentiment']})")
                else:
                    st.warning("내용 입력 필요")

    st.markdown("#### 학습 내역")
    templates = load_json_data("templates.json")
    owner_data = [t for t in templates if t.get("metadata", {}).get("tone") == "owner_custom"]

    if owner_data:
        for idx, item in enumerate(owner_data):
            st.text(f"#{idx + 1}: {item['content']}")
    else:
        st.caption("데이터 없음")