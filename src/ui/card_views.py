import streamlit as st
import pandas as pd
from src.workflow import build_graph
from src.data_manager import save_completed_review, save_drafts


# ------------------------------------------------------------------------------
# [Helper] 상태 배지 HTML 생성 함수 (색상 복구)
# ------------------------------------------------------------------------------
def get_status_badge_html(status):
    # CSS 클래스는 src/ui/styles.py에 정의되어 있음
    if status == "saved":
        return '<span class="status-badge badge-saved">완료</span>'
    elif status == "generated":
        return '<span class="status-badge badge-generated">진행중</span>'
    else:
        return '<span class="status-badge badge-draft">대기</span>'


# ==============================================================================
# [공통] 답글 작성/수정 모달
# ==============================================================================
@st.dialog("답글 작성 스튜디오", width="large")
def open_reply_modal(review, selected_tone):
    st.caption("고객 정보와 리뷰를 확인하고 AI 답글을 작성하세요.")
    st.markdown("---")

    col_left, col_right = st.columns([1, 1], gap="large")

    # --- [왼쪽] 고객 리뷰 & 정보 수정 영역 ---
    with col_left:
        st.markdown("#### 고객 정보 및 리뷰")

        c_name, c_badge = st.columns([0.6, 0.4])
        with c_name:
            if "customer_name" not in review: review["customer_name"] = ""

            new_name = st.text_input(
                "고객명",
                value=review["customer_name"],
                placeholder="고객명 입력 (예: 홍길동)",
                key=f"modal_name_{review['id']}"
            )
            if new_name != review["customer_name"]:
                review["customer_name"] = new_name
                save_drafts(st.session_state.active_reviews)

        with c_badge:
            if review.get("sentiment"):
                icon = ":material/sentiment_satisfied:" if review[
                                                               "sentiment"] == "positive" else ":material/sentiment_dissatisfied:"
                text = "긍정" if review["sentiment"] == "positive" else "부정"
                st.info(f"분석: **{icon} {text}**")
            else:
                st.empty()

        new_text = st.text_area(
            "리뷰 내용",
            value=review["text"],
            height=350,
            key=f"modal_review_text_{review['id']}",
            placeholder="여기에 고객 리뷰를 입력하세요..."
        )
        if new_text != review["text"]:
            review["text"] = new_text
            save_drafts(st.session_state.active_reviews)

    # --- [오른쪽] AI 답글 생성 영역 ---
    with col_right:
        st.markdown(f"#### AI 답글 ({selected_tone})")

        if not review.get("reply"):
            st.markdown("<br>" * 5, unsafe_allow_html=True)
            st.info("왼쪽 정보를 확인 후 생성 버튼을 눌러주세요.")

            if st.button("AI 답글 생성", icon=":material/bolt:", type="primary", use_container_width=True):
                if review["text"]:
                    with st.spinner("생성 중..."):
                        save_drafts(st.session_state.active_reviews)
                        app = build_graph()
                        result = app.invoke({
                            "review_text": review["text"],
                            "customer_name": review.get("customer_name", ""),
                            "tone": selected_tone,
                            "user_feedback": None
                        })
                        review["reply"] = result["final_reply"]
                        review["sentiment"] = result["sentiment"]
                        review["status"] = "generated"
                        save_drafts(st.session_state.active_reviews)
                        st.rerun()
                else:
                    st.warning("왼쪽에 고객 리뷰를 입력해주세요.")

        else:
            reply_text = st.text_area(
                "답글 에디터",
                value=review["reply"],
                height=350,
                key=f"modal_reply_text_{review['id']}",
                label_visibility="collapsed"
            )

            if reply_text != review["reply"]:
                review["reply"] = reply_text
                save_drafts(st.session_state.active_reviews)

            st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
            c1, c2 = st.columns([1, 1])

            with c1:
                if st.button("다시 쓰기", icon=":material/refresh:", use_container_width=True):
                    with st.spinner("수정 중..."):
                        save_drafts(st.session_state.active_reviews)
                        app = build_graph()
                        result = app.invoke({
                            "review_text": review["text"],
                            "customer_name": review.get("customer_name", ""),
                            "tone": selected_tone,
                            "user_feedback": "다른 표현으로 다시 써줘"
                        })
                        review["reply"] = result["final_reply"]
                        save_drafts(st.session_state.active_reviews)
                        st.rerun()

            with c2:
                if st.button("저장 완료", icon=":material/check:", type="primary", use_container_width=True):
                    save_data = {
                        "id": review["id"],
                        "customer_name": review.get("customer_name", ""),
                        "review_text": review["text"],
                        "reply_text": review["reply"],
                        "tone": selected_tone,
                        "sentiment": review.get("sentiment", "unknown"),
                        "timestamp": str(pd.Timestamp.now())
                    }
                    save_completed_review(save_data)
                    review["status"] = "saved"
                    save_drafts(st.session_state.active_reviews)

                    del st.session_state['edit_target_id']
                    st.toast("저장되었습니다.")
                    st.rerun()


# ==============================================================================
# [뷰 1] 리스트 뷰 (배지 적용)
# ==============================================================================
def render_list_view(reviews, selected_tone, ids_to_remove):
    h1, h2, h3, h4, h5 = st.columns([0.5, 1.5, 2, 1, 0.5], vertical_alignment="center")
    h1.caption("상태")
    h2.caption("고객명")
    h3.caption("내용")
    h4.caption("감정")
    h5.caption("삭제")

    for review in reviews:
        with st.container():
            c1, c2, c3, c4, c5 = st.columns([0.5, 1.5, 2, 1, 0.5], gap="small", vertical_alignment="center")

            # [FIX] 상태를 컬러 배지 HTML로 복구
            with c1:
                badge_html = get_status_badge_html(review["status"])
                st.markdown(badge_html, unsafe_allow_html=True)

            with c2:
                name = review.get("customer_name", "").strip()
                if not name: name = "-"
                st.markdown(f"**{name}**")

            with c3:
                display_text = review["text"][:30] + "..." if len(review["text"]) > 30 else review["text"]
                if not display_text: display_text = "(내용 없음)"

                if st.button(f"{display_text}", key=f"list_{review['id']}", use_container_width=True):
                    st.session_state['edit_target_id'] = review['id']
                    st.rerun()

            with c4:
                if review.get("sentiment") == "positive":
                    st.markdown(":material/sentiment_satisfied: 긍정")
                elif review.get("sentiment") == "negative":
                    st.markdown(":material/sentiment_dissatisfied: 부정")
                else:
                    st.markdown("-")

            with c5:
                if st.button("", icon=":material/delete:", key=f"del_l_{review['id']}"):
                    ids_to_remove.append(review['id'])

            st.markdown("<hr style='margin: 5px 0;'>", unsafe_allow_html=True)


# ==============================================================================
# [뷰 2] 카드 뷰 (배지 적용)
# ==============================================================================
def render_grid_view(reviews, selected_tone, ids_to_remove):
    for i in range(0, len(reviews), 4):
        row_reviews = reviews[i: i + 4]
        cols = st.columns(4)

        for j, review in enumerate(row_reviews):
            with cols[j]:
                with st.container(border=True):

                    c_badge, c_del = st.columns([0.8, 0.2], vertical_alignment="center")

                    # [FIX] 상태를 컬러 배지 HTML로 복구
                    with c_badge:
                        badge_html = get_status_badge_html(review["status"])
                        st.markdown(badge_html, unsafe_allow_html=True)

                    with c_del:
                        if st.button("", icon=":material/delete:", key=f"del_g_{review['id']}", help="삭제"):
                            ids_to_remove.append(review['id'])

                    st.markdown("<div style='margin-bottom: 10px;'></div>", unsafe_allow_html=True)

                    name = review.get("customer_name", "").strip()
                    if not name: name = "미입력"
                    st.markdown(f"👤 **{name}**")

                    display_text = review["text"][:50] + "..." if len(review["text"]) > 50 else review["text"]
                    if not display_text: display_text = "클릭하여 작성"

                    if st.button(display_text, key=f"card_btn_{review['id']}", use_container_width=True):
                        st.session_state['edit_target_id'] = review['id']
                        st.rerun()

                    st.markdown("<div style='margin-bottom: 8px;'></div>", unsafe_allow_html=True)

                    if review.get("sentiment"):
                        if review["sentiment"] == "positive":
                            st.caption(":material/sentiment_satisfied: 긍정적 리뷰")
                        else:
                            st.caption(":material/sentiment_dissatisfied: 부정적 리뷰")
                    else:
                        st.caption("-")