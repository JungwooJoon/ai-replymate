import streamlit as st


def apply_custom_style():
    st.markdown("""
        <style>
        /* [기본 설정] 폰트 및 배경 */
        @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
        html, body, [class*="css"] { font-family: 'Pretendard', sans-serif; }
        .stApp { background-color: #F8F9FA; }

        /* [카드] Container 디자인 */
        [data-testid="stVerticalBlockBorderWrapper"] {
            background-color: #FFFFFF;
            border-radius: 16px;
            border: 1px solid #E9ECEF;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);
            padding: 20px;
            transition: transform 0.2s ease-in-out;
        }
        [data-testid="stVerticalBlockBorderWrapper"]:hover {
            box-shadow: 0 8px 16px rgba(0, 0, 0, 0.06);
            transform: translateY(-2px);
        }

        /* [배지] 상태 배지 스타일 */
        .status-badge {
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 700;
            display: inline-block;
            white-space: nowrap;
        }
        .badge-saved { background-color: #E3F9E5; color: #1B5E20; border: 1px solid #C3E6CB; }
        .badge-generated { background-color: #FFF3CD; color: #856404; border: 1px solid #FFEEBA; }
        .badge-draft { background-color: #F1F3F5; color: #495057; border: 1px solid #DEE2E6; }

        /* [입력창] Textarea */
        .stTextArea textarea {
            background-color: #FAFAFA;
            border: 1px solid #E9ECEF;
            border-radius: 10px;
            font-size: 14px;
            color: #333;
        }

        /* [버튼] Button */
        .stButton button {
            border-radius: 10px;
            font-weight: 600;
            border: none;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            transition: all 0.2s;
        }

        /* [아이콘 버튼] */
        div[data-testid="column"] button {
            background-color: #F8F9FA;
            border: 1px solid #E9ECEF;
            color: #495057;
            padding: 0.25rem 0.5rem;
            min-height: 0px;
        }
        div[data-testid="column"] button:hover {
            background-color: #E9ECEF;
            color: #212529;
        }

        /* [메트릭] Metric Card */
        [data-testid="stMetric"] {
            background-color: #FFFFFF;
            padding: 15px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.04);
            border: 1px solid #F1F3F5;
        }

        /* [모바일] 카드 내부 줄바꿈 방지 */
        [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stHorizontalBlock"] {
            flex-wrap: nowrap !important;
        }
        [data-testid="stVerticalBlockBorderWrapper"] [data-testid="column"] {
            min-width: 0 !important;
            flex: 1 !important;
            width: auto !important;
        }
        [data-testid="stVerticalBlockBorderWrapper"] button {
            padding-left: 5px !important;
            padding-right: 5px !important;
        }

        /* [라디오 버튼 -> 카드형 버튼] (대시보드/카드뷰 공통) */
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