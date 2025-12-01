import streamlit as st


def apply_custom_style():
    st.markdown("""
        <style>
        /* 1. 전체 폰트 및 배경 */
        @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');

        html, body, [class*="css"] {
            font-family: 'Pretendard', sans-serif;
        }

        .stApp {
            background-color: #F8F9FA; /* 아주 연한 회색 배경 */
        }

        /* 2. 카드(Container) 디자인 - 그림자와 둥근 모서리 강화 */
        [data-testid="stVerticalBlockBorderWrapper"] {
            background-color: #FFFFFF;
            border-radius: 16px;
            border: 1px solid #E9ECEF;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03); /* 부드러운 그림자 */
            padding: 20px;
            transition: transform 0.2s ease-in-out;
        }

        /* 마우스 올렸을 때 살짝 떠오르는 효과 */
        [data-testid="stVerticalBlockBorderWrapper"]:hover {
            box-shadow: 0 8px 16px rgba(0, 0, 0, 0.06);
            transform: translateY(-2px);
        }

        /* 3. 상태 배지 (Badge) 스타일 */
        .status-badge {
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 700;
            display: inline-block;
        }

        .badge-saved {
            background-color: #E3F9E5; /* 연한 초록 */
            color: #1B5E20;           /* 진한 초록 */
            border: 1px solid #C3E6CB;
        }

        .badge-generated {
            background-color: #FFF3CD; /* 연한 노랑/주황 */
            color: #856404;           /* 진한 노랑 */
            border: 1px solid #FFEEBA;
        }

        .badge-draft {
            background-color: #F1F3F5; /* 연한 회색 */
            color: #495057;           /* 진한 회색 */
            border: 1px solid #DEE2E6;
        }

        /* 4. 입력창 스타일 - 더 깔끔하게 */
        .stTextArea textarea {
            background-color: #FAFAFA;
            border: 1px solid #E9ECEF;
            border-radius: 10px;
            font-size: 14px;
            color: #333;
        }
        .stTextArea textarea:focus {
            border-color: #FF4B4B;
            box-shadow: 0 0 0 2px rgba(255, 75, 75, 0.1);
        }

        /* 5. 버튼 스타일 */
        .stButton button {
            border-radius: 10px;
            font-weight: 600;
            border: none;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            transition: all 0.2s;
        }

        /* 6. 아이콘 버튼 (수정/삭제) 스타일 */
        div[data-testid="column"] button {
            background-color: #F8F9FA;
            border: 1px solid #E9ECEF;
            color: #495057;
        }
        div[data-testid="column"] button:hover {
            background-color: #E9ECEF;
            color: #212529;
        }

        /* 7. 메트릭 카드 */
        [data-testid="stMetric"] {
            background-color: #FFFFFF;
            padding: 15px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.04);
            border: 1px solid #F1F3F5;
        }
        </style>
    """, unsafe_allow_html=True)