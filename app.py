import streamlit as st
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

# 페이지 설정
st.set_page_config(
    page_title="AI ReplyMate",
    page_icon="💬",
    layout="wide"
)


def main():
    st.title("💬 AI ReplyMate: 사장님을 위한 리뷰 답글 봇")

    # 사이드바 설정
    with st.sidebar:
        st.header("설정 (Settings)")
        tone = st.selectbox("답글 톤 설정", ["정중한", "친근한", "유머러스한"])
        st.info(f"현재 설정된 톤: **{tone}**")
        st.divider()
        st.write("Developed by 4학년 졸업반")

    # 메인 화면 탭 구성
    tab1, tab2, tab3 = st.tabs(["리뷰 답글 생성", "대시보드", "데이터 관리"])

    with tab1:
        st.subheader("리뷰 입력")
        review_input = st.text_area("고객 리뷰를 복사해서 넣어주세요.", height=150)

        if st.button("답글 생성하기 ✨"):
            if review_input:
                with st.spinner("AI가 감정을 분석하고 답글을 작성 중입니다..."):
                    # 추후 여기에 LangGraph 연결
                    import time
                    time.sleep(1)  # 임시 대기
                    st.success("생성 완료!")

                    # 임시 결과 보여주기
                    st.markdown("### 🤖 AI 추천 답글")
                    st.info(f"(톤: {tone}) 고객님, 소중한 리뷰 남겨주셔서 감사합니다! ...")
            else:
                st.warning("리뷰 내용을 입력해주세요.")

    with tab2:
        st.subheader("리뷰 분석 대시보드")
        st.write("준비 중입니다...")

    with tab3:
        st.subheader("과거 데이터 및 메뉴 관리")
        st.write("ChromaDB 관리 화면이 들어갈 곳입니다.")


if __name__ == "__main__":
    main()