import streamlit as st
import pandas as pd
from src.workflow import build_graph
from src.data_manager import save_completed_review, save_drafts


def get_status_badge_html(status):
    if status == "saved":
        return '<span class="status-badge badge-saved">완료</span>'
    elif status == "generated":
        return '<span class="status-badge badge-generated">진행중</span>'
    else:
        return '<span class="status-badge badge-draft">대기</span>'


def get_menu_badge_html(menu_name):
    if menu_name and menu_name != "null":
        return f'<span style="background-color:#E3F2FD; color:#1565C0; padding:4px 8px; border-radius:6px; font-size:12px; font-weight:600; border:1px solid #BBDEFB;">{menu_name}</span>'
    return ""


def update_and_save(review_id, field, new_value):
    for r in st.session_state.active_reviews:
        if r['id'] == review_id:
            r[field] = new_value
            break
    save_drafts(st.session_state.active_reviews)


# ------------------------------------------------------------------------------
# [Sub-Component] 왼쪽 영역 (리뷰 내용) - 코드 중복 방지용
# ------------------------------------------------------------------------------
def _render_review_area(review):
    st.markdown("#### 고객 정보 및 리뷰")

    c_name, c_menu = st.columns(2)

    with c_name:
        if "customer_name" not in review: review["customer_name"] = ""
        new_name = st.text_input(
            "고객명",
            value=review["customer_name"],
            placeholder="예: 홍길동",
            key=f"modal_name_{review['id']}"
        )
        if new_name != review["customer_name"]:
            review["customer_name"] = new_name
            update_and_save(review['id'], "customer_name", new_name)

    with c_menu:
        if "menu_name" not in review: review["menu_name"] = ""
        new_menu = st.text_input(
            "메뉴명 (AI 검색용)",
            value=review["menu_name"],
            placeholder="예: 치즈돈까스",
            key=f"modal_menu_{review['id']}",
            help="비워두면 AI가 리뷰에서 자동으로 추측합니다."
        )
        if new_menu != review["menu_name"]:
            review["menu_name"] = new_menu
            update_and_save(review['id'], "menu_name", new_menu)

    if review.get("sentiment"):
        icon = ":material/sentiment_satisfied:" if review[
                                                       "sentiment"] == "positive" else ":material/sentiment_dissatisfied:"
        text = "긍정" if review["sentiment"] == "positive" else "부정"
        st.info(f"AI 분석: **{icon} {text}**")

    new_text = st.text_area(
        "리뷰 내용",
        value=review["text"],
        height=350,
        key=f"modal_review_text_{review['id']}",
        placeholder="여기에 고객 리뷰를 입력하세요..."
    )
    if new_text != review["text"]:
        review["text"] = new_text
        update_and_save(review['id'], "text", new_text)


# ------------------------------------------------------------------------------
# [Sub-Component] 오른쪽 영역 (답글 작성) - 코드 중복 방지용
# ------------------------------------------------------------------------------
def _render_reply_area(review, selected_tone, store_name):
    st.markdown(f"#### AI 답글 ({selected_tone})")

    if not review.get("reply"):
        st.markdown("<br>" * 5, unsafe_allow_html=True)
        st.info("정보 확인 후 생성 버튼을 눌러주세요.")

        if st.button("AI 답글 생성", icon=":material/bolt:", type="primary", use_container_width=True,
                     key=f"btn_create_{review['id']}"):
            if review["text"]:
                with st.spinner("생성 중..."):
                    save_drafts(st.session_state.active_reviews)

                    app = build_graph()
                    result = app.invoke({
                        "review_text": review["text"],
                        "customer_name": review.get("customer_name", ""),
                        "manual_menu": review.get("menu_name", ""),
                        "store_name": store_name,
                        "tone": selected_tone,
                        "user_feedback": None
                    })
                    review["reply"] = result["final_reply"]
                    review["sentiment"] = result["sentiment"]
                    review["status"] = "generated"

                    extracted = result.get("extracted_menu")
                    if not review["menu_name"] and extracted and extracted != "null":
                        review["menu_name"] = extracted
                        update_and_save(review['id'], "menu_name", extracted)

                    save_drafts(st.session_state.active_reviews)
                    st.rerun()
            else:
                st.warning("리뷰 내용을 입력해주세요.")

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
            update_and_save(review['id'], "reply", reply_text)

        st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
        c1, c2 = st.columns([1, 1])

        with c1:
            if st.button("다시 쓰기", icon=":material/refresh:", use_container_width=True, key=f"btn_retry_{review['id']}"):
                with st.spinner("수정 중..."):
                    save_drafts(st.session_state.active_reviews)
                    app = build_graph()
                    result = app.invoke({
                        "review_text": review["text"],
                        "customer_name": review.get("customer_name", ""),
                        "manual_menu": review.get("menu_name", ""),
                        "store_name": store_name,
                        "tone": selected_tone,
                        "user_feedback": "다른 표현으로 다시 써줘"
                    })
                    review["reply"] = result["final_reply"]

                    widget_key = f"modal_reply_text_{review['id']}"
                    if widget_key in st.session_state:
                        del st.session_state[widget_key]

                    save_drafts(st.session_state.active_reviews)
                    st.rerun()

        with c2:
            if st.button("저장 완료", icon=":material/check:", type="primary", use_container_width=True,
                         key=f"btn_finish_{review['id']}"):
                save_data = {
                    "id": review["id"],
                    "customer_name": review.get("customer_name", ""),
                    "menu_name": review.get("menu_name", ""),
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
# [공통] 메인 모달 함수 (여기가 수정되었습니다!)
# ==============================================================================
@st.dialog("답글 작성 스튜디오", width="large")
def open_reply_modal(review, selected_tone, store_name, view_mode="desktop"):  # [FIX] 4개 인자 받음
    st.caption("고객 정보와 리뷰를 확인하고 AI 답글을 작성하세요.")

    # [LOGIC] 뷰 모드에 따라 레이아웃 분기 (모바일 최적화)
    if view_mode == "mobile":
        # 모바일용: 탭으로 분리
        tab1, tab2 = st.tabs([":material/person: 리뷰 확인", ":material/edit_note: 답글 작성"])

        with tab1:
            _render_review_area(review)

        with tab2:
            _render_reply_area(review, selected_tone, store_name)

    else:
        # 데스크탑용: 좌우 분할
        st.markdown("---")
        col_left, col_right = st.columns([1, 1], gap="large")

        with col_left:
            _render_review_area(review)

        with col_right:
            _render_reply_area(review, selected_tone, store_name)


# ==============================================================================
# [뷰 1] 리스트 뷰
# ==============================================================================
def render_list_view(reviews, selected_tone, store_name, ids_to_remove):
    h1, h2, h3, h4, h5 = st.columns([0.5, 1.5, 2, 1, 0.5], vertical_alignment="center")
    h1.caption("상태")
    h2.caption("고객명")
    h3.caption("내용")
    h4.caption("감정")
    h5.caption("삭제")

    for review in reviews:
        with st.container():
            c1, c2, c3, c4, c5 = st.columns([0.5, 1.5, 2, 1, 0.5], gap="small", vertical_alignment="center")

            with c1:
                badge_html = get_status_badge_html(review["status"])
                st.markdown(badge_html, unsafe_allow_html=True)

            with c2:
                name = review.get("customer_name", "").strip()
                if not name: name = "-"
                st.markdown(f"**{name}**")

            with c3:
                menu_badge = get_menu_badge_html(review.get("menu_name", ""))
                display_text = review["text"][:30] + "..." if len(review["text"]) > 30 else review["text"]
                if not display_text: display_text = "(내용 없음)"

                if menu_badge:
                    st.markdown(menu_badge, unsafe_allow_html=True)

                if st.button(f"{display_text}", key=f"list_{review['id']}", use_container_width=True):
                    st.session_state['edit_target_id'] = review['id']
                    # [NEW] 데스크탑 모드로 설정
                    st.session_state['target_view_mode'] = 'desktop'
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
# [뷰 2] 카드 뷰
# ==============================================================================
def render_grid_view(reviews, selected_tone, store_name, ids_to_remove):
    for i in range(0, len(reviews), 4):
        row_reviews = reviews[i: i + 4]
        cols = st.columns(4)

        for j, review in enumerate(row_reviews):
            with cols[j]:
                with st.container(border=True):
                    c_badge, c_del = st.columns([0.8, 0.2], vertical_alignment="center")

                    with c_badge:
                        badge_html = get_status_badge_html(review["status"])
                        st.markdown(badge_html, unsafe_allow_html=True)

                    with c_del:
                        if st.button("", icon=":material/delete:", key=f"del_g_{review['id']}", help="삭제"):
                            ids_to_remove.append(review['id'])

                    st.markdown("<div style='margin-bottom: 10px;'></div>", unsafe_allow_html=True)

                    name = review.get("customer_name", "").strip()
                    if not name: name = "미입력"
                    st.markdown(f":material/person: **{name}**")

                    menu_badge = get_menu_badge_html(review.get("menu_name", ""))
                    if menu_badge:
                        st.markdown(menu_badge, unsafe_allow_html=True)
                        st.markdown("<div style='margin-bottom: 5px;'></div>", unsafe_allow_html=True)

                    display_text = review["text"][:50] + "..." if len(review["text"]) > 50 else review["text"]
                    if not display_text: display_text = "클릭하여 작성"

                    if st.button(display_text, key=f"card_btn_{review['id']}", use_container_width=True):
                        st.session_state['edit_target_id'] = review['id']
                        # [NEW] 모바일 모드로 설정
                        st.session_state['target_view_mode'] = 'mobile'
                        st.rerun()

                    st.markdown("<div style='margin-bottom: 8px;'></div>", unsafe_allow_html=True)

                    if review.get("sentiment"):
                        if review["sentiment"] == "positive":
                            st.caption(":material/sentiment_satisfied: 긍정적 리뷰")
                        else:
                            st.caption(":material/sentiment_dissatisfied: 부정적 리뷰")
                    else:
                        st.caption("-")