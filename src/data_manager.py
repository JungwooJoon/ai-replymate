import json
import pandas as pd
import platform
from pathlib import Path
from wordcloud import WordCloud
import matplotlib.pyplot as plt

# 경로 설정
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
SAVED_REVIEWS_FILE = "saved_reviews.json"
TEMPLATES_FILE = "templates.json"


def _get_path(filename):
    return DATA_DIR / filename


def load_json_data(filename):
    """JSON 파일 로드"""
    file_path = _get_path(filename)
    if not file_path.exists():
        # 파일이 없으면 빈 리스트 반환
        return []
    with open(file_path, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def save_json_data(filename, data):
    """JSON 파일 저장"""
    file_path = _get_path(filename)
    # data 폴더가 없으면 생성
    if not DATA_DIR.exists():
        DATA_DIR.mkdir(parents=True)

    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"[INFO] Data saved to {filename}")


def save_completed_review(review_data):
    """[Req 2] 완료된 리뷰 및 답글 저장"""
    current_data = load_json_data(SAVED_REVIEWS_FILE)
    current_data.append(review_data)
    save_json_data(SAVED_REVIEWS_FILE, current_data)


def generate_analytics_data():
    """[Req 3] 저장된 완료 리뷰 기반 통계 데이터 생성"""
    # templates.json이 아닌 saved_reviews.json을 로드
    reviews = load_json_data(SAVED_REVIEWS_FILE)

    df = pd.DataFrame(reviews)

    if df.empty:
        return pd.DataFrame(), None

    # 워드클라우드용 텍스트 (리뷰 내용 기준)
    text_corpus = " ".join(df['review_text'].astype(str).tolist())

    font_path = get_korean_font_path()

    try:
        wc = WordCloud(
            font_path=font_path,
            background_color="white",
            width=800,
            height=400,
            colormap="viridis"
        ).generate(text_corpus)
    except Exception as e:
        print(f"[ERROR] WordCloud generation failed: {e}")
        wc = None

    return df, wc


def reset_app_data():
    """
    1. 저장된 완료 리뷰(saved_reviews.json) 삭제
    2. 학습된 사장님 말투(templates.json 내 owner_custom) 삭제
    """
    # 1. 완료된 리뷰 초기화
    print("[INFO] Resetting saved reviews...")
    save_json_data(SAVED_REVIEWS_FILE, [])

    # 2. 템플릿에서 학습 데이터 제거 (기본 데이터는 유지)
    templates = load_json_data(TEMPLATES_FILE)
    if templates:
        # tone이 'owner_custom'이 아닌 것만 남김 (기본 데이터 보존)
        base_templates = [
            t for t in templates
            if t.get("metadata", {}).get("tone") != "owner_custom"
        ]

        # 삭제된 항목이 있을 때만 저장
        if len(templates) != len(base_templates):
            save_json_data(TEMPLATES_FILE, base_templates)
            print(f"[INFO] Removed {len(templates) - len(base_templates)} custom templates.")
        else:
            print("[INFO] No custom templates to remove.")

    return True


def get_korean_font_path():
    """OS별 한글 폰트 경로"""
    system_name = platform.system()
    if system_name == "Windows":
        return "c:/Windows/Fonts/malgun.ttf"
    elif system_name == "Darwin":
        return "/System/Library/Fonts/AppleGothic.ttf"
    else:
        return "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"
