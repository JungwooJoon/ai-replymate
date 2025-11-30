import streamlit as st


def apply_custom_style():
    st.markdown("""
        <style>
        /* 1. 전체 배경색 */
        .stApp { background-color: #F5F7F9; }

        /* 2. 사이드바 스타일 */
        [data-testid="stSidebar"] { background-color: #2C3E50; }
        [data-testid="stSidebar"] * { color: #ffffff !important; }

        /* 3. 카드(Container) 스타일 */
        [data-testid="stVerticalBlockBorderWrapper"] {
            background-color: #FFFFFF;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
            border: 1px solid #E1E4E8;
            padding: 16px;
        }

        /* 4. 입력창 스타일 */
        .stTextArea textarea {
            background-color: #F8F9FA;
            border: 1px solid #E1E4E8;
            border-radius: 8px;
        }

        /* 5. 버튼 스타일 */
        .stButton button {
            border-radius: 8px;
            font-weight: 600;
        }

        /* 6. 메트릭 카드 스타일 */
        [data-testid="stMetric"] {
            background-color: #FFFFFF;
            padding: 10px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        </style>
    """, unsafe_allow_html=True)