import streamlit as st
import uuid
from src.data_manager import save_drafts, load_drafts, load_json_data
from src.ui.card_views import render_list_view, render_grid_view, open_reply_modal  # open_reply_modal 임포트 필수


def render_review_cards_tab(selected_tone):
    # 1. 데이터 로드 (기존 동일)
    if "active_reviews" not in st.session_state:
        st.session_state.active_reviews = []
        drafts = load_drafts()
        if drafts:
            for d in drafts:
                if "customer_name" not in d: d["customer_name"] = ""
        active_drafts = [d for d in drafts if d.get("status") != "saved"] if drafts else []
        saved_history = load_json_data("saved_reviews.json")
        converted_history = []
        if saved_history:
            for item in saved_history:
                converted_history.append({
                    "id": item.get("id", str(uuid.uuid4())),
                    "customer_name": item.get("customer_name", ""),
                    "text": item.get("review_text", ""),
                    "reply": item.get("reply_text", ""),
                    "sentiment": item.get("sentiment"),
                    "status": "saved"
                })
        st.session_state.active_reviews = active_drafts + converted_history[::-1]

        # -------------------------------------------------------------
    # [NEW] 모달 자동 열기 로직 (핵심)
    # -------------------------------------------------------------
    if "edit_target_id" in st.session_state and st.session_state["edit_target_id"]:
        # 해당 ID를 가진 리뷰 찾기
        target_review = next(
            (r for r in st.session_state.active_reviews if r['id'] == st.session_state["edit_target_id"]), None)

        if target_review:
            # 모달 열기
            open_reply_modal(target_review, selected_tone)
        else:
            # 리뷰가 없으면(삭제됨 등) ID 초기화
            del st.session_state["edit_target_id"]
            st.rerun()

    # 2. 상단 헤더
    c_title, c_view, c_add = st.columns([0.5, 0.3, 0.2], vertical_alignment="center")

    with c_title:
        st.markdown("### :material/inbox: 리뷰 워크스페이스")

    with c_view:
        view_mode = st.radio(
            "보기 모드",
            ["리스트", "카드"],
            horizontal=True,
            label_visibility="collapsed"
        )

    with c_add:
        if st.button("추가", icon=":material/add:", type="primary", use_container_width=True):
            new_review = {
                "id": str(uuid.uuid4()),
                "customer_name": "",
                "text": "",
                "reply": None,
                "status": "draft"
            }
            st.session_state.active_reviews.insert(0, new_review)
            save_drafts(st.session_state.active_reviews)

            # [추가] 생성 즉시 모달 열기
            st.session_state["edit_target_id"] = new_review["id"]
            st.rerun()

    # 3. 필터 UI 및 로직
    with st.expander("🔍 필터 및 검색 옵션", expanded=False, icon=":material/filter_list:"):
        f_col1, f_col2 = st.columns(2)
        with f_col1:
            status_filter = st.multiselect(
                "진행 상태",
                options=["대기 (draft)", "진행 (generated)", "완료 (saved)"],
                default=["대기 (draft)", "진행 (generated)", "완료 (saved)"],
            )
        with f_col2:
            sentiment_filter = st.multiselect(
                "감정 분석",
                options=["긍정 (Positive)", "부정 (Negative)", "미분석"],
                default=["긍정 (Positive)", "부정 (Negative)", "미분석"]
            )

    target_statuses = []
    if "대기 (draft)" in status_filter: target_statuses.append("draft")
    if "진행 (generated)" in status_filter: target_statuses.append("generated")
    if "완료 (saved)" in status_filter: target_statuses.append("saved")

    target_sentiments = []
    include_none_sentiment = "미분석" in sentiment_filter
    if "긍정 (Positive)" in sentiment_filter: target_sentiments.append("positive")
    if "부정 (Negative)" in sentiment_filter: target_sentiments.append("negative")

    filtered_reviews = []
    for r in st.session_state.active_reviews:
        if r["status"] in target_statuses:
            s = r.get("sentiment")
            if s in target_sentiments:
                filtered_reviews.append(r)
            elif s is None and include_none_sentiment:
                filtered_reviews.append(r)

    st.markdown("---")

    # 4. 뷰 렌더링 호출
    ids_to_remove = []

    if not filtered_reviews:
        st.info("조건에 맞는 리뷰가 없습니다.")
    else:
        if view_mode == "리스트":
            render_list_view(filtered_reviews, selected_tone, ids_to_remove)
        else:
            render_grid_view(filtered_reviews, selected_tone, ids_to_remove)

    # 5. 삭제 처리
    if ids_to_remove:
        st.session_state.active_reviews = [
            r for r in st.session_state.active_reviews
            if r['id'] not in ids_to_remove
        ]
        save_drafts(st.session_state.active_reviews)
        st.rerun()