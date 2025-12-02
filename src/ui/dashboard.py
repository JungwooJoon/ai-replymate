import streamlit as st
import pandas as pd
# [삭제] import matplotlib.pyplot as plt (이제 필요 없음)
from wordcloud import WordCloud
from src.data_manager import generate_analytics_data, get_korean_font_path


def render_dashboard_tab():
    st.markdown("### :material/analytics: 대시보드")

    # CSS 스타일 (라디오 버튼) - 기존 유지
    st.markdown("""
        <style>
        div.row-widget.stRadio > div {
            flex-direction: row;
            gap: 12px;
            width: 100%;
        }
        div.row-widget.stRadio > div > label {
            background-color: #FFFFFF;
            padding: 12px 20px;
            border-radius: 12px;
            border: 1px solid #E1E4E8;
            width: 100%;
            text-align: center;
            cursor: pointer;
            box-shadow: 0 2px 4px rgba(0,0,0,0.02);
            transition: all 0.2s;
            justify-content: center;
            font-weight: 600;
            color: #4A5568;
        }
        div.row-widget.stRadio > div > label:hover {
            border-color: #FF4B4B;
            background-color: #FFF5F5;
            color: #FF4B4B;
        }
        div.row-widget.stRadio > div > label > div:first-child {
            display: none;
        }
        div.row-widget.stRadio > div > label[data-baseweb="radio"] {
            border-color: #FF4B4B !important;
            background-color: #FF4B4B !important;
            color: white !important;
        }
        </style>
    """, unsafe_allow_html=True)

    df, _ = generate_analytics_data()

    if not df.empty:
        with st.container(border=True):
            f_col1, f_col2 = st.columns(2)

            with f_col1:
                filter_sentiment = st.radio(
                    "분석 필터",
                    ["전체", "긍정", "부정"],
                    horizontal=True,
                    label_visibility="collapsed",
                    key="dash_sent"
                )

            with f_col2:
                filter_period = st.radio(
                    "기간 설정",
                    ["1일", "7일", "1개월", "전체"],
                    horizontal=True,
                    label_visibility="collapsed",
                    key="dash_period",
                    index=3
                )

        # 데이터 필터링 로직 (기존 유지)
        filtered_df = df.copy()

        if 'timestamp' in filtered_df.columns:
            filtered_df['timestamp'] = pd.to_datetime(filtered_df['timestamp'])
            now = pd.Timestamp.now()

            if filter_period == "1일":
                start_date = now - pd.Timedelta(days=1)
                filtered_df = filtered_df[filtered_df['timestamp'] >= start_date]
            elif filter_period == "7일":
                start_date = now - pd.Timedelta(days=7)
                filtered_df = filtered_df[filtered_df['timestamp'] >= start_date]
            elif filter_period == "1개월":
                start_date = now - pd.Timedelta(days=30)
                filtered_df = filtered_df[filtered_df['timestamp'] >= start_date]

        if 'sentiment' not in filtered_df.columns:
            filtered_df['sentiment'] = 'unknown'

        if filter_sentiment == "긍정":
            filtered_df = filtered_df[filtered_df['sentiment'] == 'positive']
        elif filter_sentiment == "부정":
            filtered_df = filtered_df[filtered_df['sentiment'] == 'negative']

        st.divider()

        if filtered_df.empty:
            st.warning("선택하신 기간/조건에 해당하는 데이터가 없습니다.")
            return

        c1, c2, c3 = st.columns(3)
        c1.metric("리뷰 수", f"{len(filtered_df)}건")

        pos_ratio = (len(filtered_df[filtered_df['sentiment'] == 'positive']) / len(filtered_df) * 100) if len(
            filtered_df) > 0 else 0
        c2.metric("기간 내 긍정 비율", f"{pos_ratio:.1f}%")

        latest_date = filtered_df['timestamp'].max().strftime('%m-%d %H:%M') if not filtered_df.empty else "-"
        c3.metric("최근 활동", latest_date)

        st.markdown("---")

        col_wc, col_table = st.columns([1, 1])

        with col_wc:
            st.markdown(f"**cs:material/cloud: 키워드 분석**")
            with st.container(border=True):
                text_corpus = " ".join(filtered_df['review_text'].astype(str).tolist())
                if text_corpus.strip():
                    font_path = get_korean_font_path()
                    try:
                        wc = WordCloud(
                            font_path=font_path,
                            background_color="white",
                            width=600,
                            height=400,
                            colormap="RdBu" if filter_sentiment == "부정" else "viridis"
                        ).generate(text_corpus)

                        # [FIX] Matplotlib(plt) 대신 st.image 사용! (훨씬 안정적)
                        # 워드클라우드 객체를 바로 이미지 배열로 변환해서 출력합니다.
                        st.image(wc.to_array(), use_container_width=True)

                    except Exception as e:
                        st.error("워드클라우드 생성 실패")
                else:
                    st.info("텍스트 데이터 부족")

        with col_table:
            st.markdown("**cs:material/table: 상세 데이터**")
            with st.container(border=True):
                display_df = filtered_df[['review_text', 'reply_text', 'sentiment', 'timestamp']].copy()
                display_df['timestamp'] = display_df['timestamp'].dt.strftime('%Y-%m-%d %H:%M')

                st.dataframe(
                    display_df,
                    width="stretch",
                    hide_index=True,
                    height=300
                )
    else:
        st.info("저장된 데이터가 없습니다.")