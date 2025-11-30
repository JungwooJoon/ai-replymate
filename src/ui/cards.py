import streamlit as st
import pandas as pd
import uuid
from src.workflow import build_graph
from src.data_manager import save_completed_review


def render_review_cards_tab(selected_tone):
    # 세션 초기화
    if "active_reviews" not in st.session_state:
        st.session_state.active_reviews = []

    total_active = len(st.session_state.active_reviews)
    saved_count = len([r for r in st.session_state.active_reviews if r['status'] == 'saved'])

    st.markdown("### 📝 리뷰 관리 워크스페이스")

    # 상단 메트릭
    m1, m2, m3 = st.columns(3)
    m1.metric("작업 중인 리뷰", f"{total_active}건", delta="실시간")
    m2.metric("처리 완료(저장)", f"{saved_count}건", delta="오늘")

    # [수정됨] use_container_width=True -> width="stretch"
    m3.button("➕ 새 리뷰 등록하기", type="primary", width="stretch", key="add_new_top")

    if st.session_state.get("add_new_top"):
        new_review = {
            "id": str(uuid.uuid4()),
            "text": "",
            "reply": None,
            "sentiment": None,
            "status": "draft"
        }
        st.session_state.active_reviews.insert(0, new_review)
        st.rerun()

    st.divider()

    # 카드 그리드
    cols = st.columns(4)

    for idx, review in enumerate(st.session_state.active_reviews):
        col = cols[idx % 4]
        with col:
            with st.container(border=True):
                # 헤더
                if review["status"] == "saved":
                    status_html = "<span style='color:green; float:right; font-size:0.8em'>● 완료 😊</span>"
                    is_disabled = True
                elif review["status"] == "generated":
                    status_html = "<span style='color:orange; float:right; font-size:0.8em'>● 생성됨</span>"
                    is_disabled = False
                else:
                    status_html = "<span style='color:gray; float:right; font-size:0.8em'>● 작성 중</span>"
                    is_disabled = False

                st.markdown(f"**Review #{idx + 1}** {status_html}", unsafe_allow_html=True)

                # 리뷰 입력
                review["text"] = st.text_area(
                    label="고객 리뷰",
                    value=review["text"],
                    height=100,
                    key=f"review_text_{review['id']}",
                    label_visibility="collapsed",
                    placeholder="리뷰 내용을 입력하세요...",
                    disabled=is_disabled
                )

                # 답글 생성 버튼
                if not is_disabled:
                    st.markdown("<div style='margin: 5px 0;'></div>", unsafe_allow_html=True)
                    # [수정됨] use_container_width=True -> width="stretch"
                    if st.button("AI 답글 생성 ✨", key=f"btn_gen_{review['id']}", width="stretch"):
                        if review["text"]:
                            with st.spinner("..."):
                                app = build_graph()
                                result = app.invoke({
                                    "review_text": review["text"],
                                    "tone": selected_tone,
                                    "user_feedback": None
                                })
                                review["reply"] = result["final_reply"]
                                review["sentiment"] = result["sentiment"]
                                review["status"] = "generated"
                                st.rerun()
                        else:
                            st.warning("내용을 입력해주세요")

                # 결과 표시 및 저장
                if review.get("reply"):
                    st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)
                    st.caption("AI 추천 답글")
                    st.text_area(
                        label="답글 결과",
                        value=review["reply"],
                        height=150,
                        key=f"reply_text_{review['id']}",
                        label_visibility="collapsed",
                        disabled=is_disabled
                    )

                    if review["status"] == "generated" and not is_disabled:
                        st.markdown("<div style='margin: 5px 0;'></div>", unsafe_allow_html=True)
                        if st.button("완료", key=f"btn_save_{review['id']}", type="primary", width="stretch"):
                            save_data = {
                                "review_text": review["text"],
                                "reply_text": review["reply"],
                                "tone": selected_tone,
                                "sentiment": review["sentiment"],
                                "timestamp": str(pd.Timestamp.now())
                            }
                            save_completed_review(save_data)
                            review["status"] = "saved"
                            st.toast("저장 완료!", icon="🎉")
                            st.rerun()