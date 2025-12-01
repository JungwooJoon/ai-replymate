import streamlit as st
import pandas as pd
import uuid
from src.workflow import build_graph
from src.data_manager import (
    save_completed_review,
    save_drafts,
    load_drafts,
    load_json_data
)


def render_review_cards_tab(selected_tone):
    # -------------------------------------------------------------
    # 데이터 로드 (기존 동일)
    # -------------------------------------------------------------
    if "active_reviews" not in st.session_state:
        st.session_state.active_reviews = []

        drafts = load_drafts()
        active_drafts = [d for d in drafts if d.get("status") != "saved"] if drafts else []

        saved_history = load_json_data("saved_reviews.json")
        converted_history = []

        if saved_history:
            for item in saved_history:
                converted_history.append({
                    "id": str(uuid.uuid4()),
                    "text": item.get("review_text", ""),
                    "reply": item.get("reply_text", ""),
                    "sentiment": item.get("sentiment"),
                    "status": "saved"
                })

        st.session_state.active_reviews = active_drafts + converted_history[::-1]
        if active_drafts or converted_history:
            st.toast("작업 공간을 복구했습니다.", icon="📂")

    # -------------------------------------------------------------
    # 상단 요약 바
    # -------------------------------------------------------------
    total_reviews_count = len(st.session_state.active_reviews)
    total_active = len([r for r in st.session_state.active_reviews if r['status'] != 'saved'])
    saved_count = len([r for r in st.session_state.active_reviews if r['status'] == 'saved'])

    st.markdown("### 📝 리뷰 관리 워크스페이스")

    m1, m2, m3 = st.columns(3)
    m1.metric("대기 중인 리뷰", f"{total_active}건", delta="To-Do")
    m2.metric("완료된 리뷰", f"{saved_count}건", delta="Done")

    m3.button("➕ 새 리뷰 등록", type="primary", width="stretch", key="add_new_top")
    if st.session_state.get("add_new_top"):
        new_review = {
            "id": str(uuid.uuid4()),
            "text": "",
            "reply": None,
            "sentiment": None,
            "status": "draft"
        }
        st.session_state.active_reviews.insert(0, new_review)
        save_drafts(st.session_state.active_reviews)
        st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # -------------------------------------------------------------
    # [FIX] 카드 그리드 레이아웃 수정 (Row-based Rendering)
    # 4개씩 끊어서 st.columns를 새로 생성해야 줄이 깨지지 않음
    # -------------------------------------------------------------

    reviews = st.session_state.active_reviews
    ids_to_remove = []

    # 4개씩 묶어서 처리 (Chunking)
    for i in range(0, len(reviews), 4):
        row_reviews = reviews[i: i + 4]  # 이번 줄에 표시할 1~4개 데이터
        cols = st.columns(4)  # 새로운 줄 생성

        for j, review in enumerate(row_reviews):
            # 실제 전체 리스트에서의 인덱스 계산
            global_idx = i + j

            with cols[j]:  # 0,1,2,3 컬럼에 순서대로 배치
                with st.container(border=True):

                    # --- [여기서부터 카드 내부 디자인 로직은 기존과 동일] ---

                    c_info, c_actions = st.columns([0.65, 0.35])

                    display_num = total_reviews_count - global_idx

                    if review["status"] == "saved":
                        badge_html = f'<span class="status-badge badge-saved">완료</span>'
                        is_disabled = True
                    elif review["status"] == "generated":
                        badge_html = f'<span class="status-badge badge-generated">생성됨</span>'
                        is_disabled = False
                    else:
                        badge_html = f'<span class="status-badge badge-draft">작성 중</span>'
                        is_disabled = False

                    with c_info:
                        st.markdown(f"**#{display_num}**&nbsp;&nbsp;{badge_html}", unsafe_allow_html=True)

                    with c_actions:
                        b1, b2 = st.columns(2)
                        with b1:
                            if review["status"] == "saved":
                                if st.button("✏️", key=f"edit_{review['id']}", help="수정하기"):
                                    review["status"] = "generated"
                                    save_drafts(st.session_state.active_reviews)
                                    st.rerun()
                            else:
                                st.write("")
                        with b2:
                            if st.button("🗑️", key=f"del_{review['id']}", help="삭제"):
                                ids_to_remove.append(review['id'])

                    # 리뷰 입력창
                    review["text"] = st.text_area(
                        label="고객 리뷰",
                        value=review["text"],
                        height=100,
                        key=f"review_text_{review['id']}",
                        label_visibility="collapsed",
                        placeholder="리뷰 내용을 입력하세요...",
                        disabled=is_disabled
                    )

                    if new_text := review["text"]:
                        if new_text != st.session_state.get(f"prev_text_{review['id']}", ""):
                            pass

                    st.markdown("<div style='margin-bottom: 8px;'></div>", unsafe_allow_html=True)

                    # 버튼
                    if not is_disabled:
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
                                    save_drafts(st.session_state.active_reviews)
                                    st.rerun()
                            else:
                                st.warning("내용 입력 필요")

                    # 결과
                    if review.get("reply"):
                        st.caption("AI 추천 답글")
                        st.text_area(
                            label="답글 결과",
                            value=review["reply"],
                            height=140,
                            key=f"reply_text_{review['id']}",
                            label_visibility="collapsed",
                            disabled=is_disabled
                        )

                        if review["status"] == "generated" and not is_disabled:
                            st.markdown("<div style='margin-top: 8px;'></div>", unsafe_allow_html=True)
                            if st.button("저장 및 완료 ✅", key=f"btn_save_{review['id']}", type="primary", width="stretch"):
                                save_data = {
                                    "review_text": review["text"],
                                    "reply_text": review["reply"],
                                    "tone": selected_tone,
                                    "sentiment": review["sentiment"],
                                    "timestamp": str(pd.Timestamp.now())
                                }
                                save_completed_review(save_data)
                                review["status"] = "saved"
                                save_drafts(st.session_state.active_reviews)
                                st.toast("저장 완료!", icon="🎉")
                                st.rerun()

    # 삭제 처리
    if ids_to_remove:
        st.session_state.active_reviews = [
            r for r in st.session_state.active_reviews
            if r['id'] not in ids_to_remove
        ]
        save_drafts(st.session_state.active_reviews)
        st.rerun()