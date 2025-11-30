import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from src.data_manager import generate_analytics_data, get_korean_font_path


def render_dashboard_tab():
    st.markdown("### 📊 대시보드 Analytics")

    df, _ = generate_analytics_data()

    if not df.empty:
        with st.container(border=True):
            filter_option = st.radio(
                "분석 필터",
                ["전체 보기", "긍정 리뷰 😊", "부정 리뷰 😡"],
                horizontal=True
            )

        filtered_df = df.copy()
        if 'sentiment' not in filtered_df.columns:
            filtered_df['sentiment'] = 'unknown'

        if filter_option == "긍정 리뷰 😊":
            filtered_df = filtered_df[filtered_df['sentiment'] == 'positive']
        elif filter_option == "부정 리뷰 😡":
            filtered_df = filtered_df[filtered_df['sentiment'] == 'negative']

        if filtered_df.empty:
            st.warning("데이터가 없습니다.")
            return

        # 메트릭
        c1, c2, c3 = st.columns(3)
        c1.metric("리뷰 수", f"{len(filtered_df)}건")
        ratio = (len(filtered_df) / len(df)) * 100
        c2.metric("비율", f"{ratio:.1f}%")
        latest_date = pd.to_datetime(filtered_df['timestamp']).max().strftime(
            '%m-%d') if 'timestamp' in filtered_df.columns else "-"
        c3.metric("최근 활동", latest_date)

        st.markdown("---")

        # 차트
        col_wc, col_table = st.columns([1, 1])

        with col_wc:
            st.markdown(f"**☁️ 키워드 분석**")
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
                            colormap="RdBu" if filter_option == "부정 리뷰 😡" else "viridis"
                        ).generate(text_corpus)

                        fig, ax = plt.subplots()
                        ax.imshow(wc, interpolation='bilinear')
                        ax.axis("off")
                        st.pyplot(fig)
                    except Exception as e:
                        st.error("워드클라우드 생성 실패")
                else:
                    st.info("텍스트 데이터 부족")

        with col_table:
            st.markdown("**📋 상세 데이터**")
            with st.container(border=True):
                st.dataframe(
                    filtered_df[['review_text', 'reply_text', 'sentiment']],
                    width="stretch",
                    hide_index=True,
                    height=300
                )
    else:
        st.info("저장된 데이터가 없습니다.")