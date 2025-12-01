import json
import platform
from pathlib import Path
import pandas as pd
from wordcloud import WordCloud

# 경로 설정
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
SAVED_REVIEWS_FILE = "saved_reviews.json"
TEMPLATES_FILE = "templates.json"
DRAFTS_FILE = "draft_reviews.json"  # [NEW] 임시 저장 파일명


def _get_path(filename):
    return DATA_DIR / filename


def load_json_data(filename):
    file_path = _get_path(filename)
    if not file_path.exists():
        return []
    with open(file_path, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def save_json_data(filename, data):
    file_path = _get_path(filename)
    if not DATA_DIR.exists():
        DATA_DIR.mkdir(parents=True)

    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    # 로그가 너무 많이 찍히지 않게 draft 저장은 print 생략 가능


def save_completed_review(review_data):
    current_data = load_json_data(SAVED_REVIEWS_FILE)
    current_data.append(review_data)
    save_json_data(SAVED_REVIEWS_FILE, current_data)


# [NEW] 임시 저장소(Draft) 관련 함수
def save_drafts(draft_data):
    """현재 작업 중인 카드 상태 저장"""
    save_json_data(DRAFTS_FILE, draft_data)


def load_drafts():
    """작업 중이던 카드 상태 불러오기"""
    return load_json_data(DRAFTS_FILE)



def get_korean_font_path():
    system_name = platform.system()
    font_path = None
    if system_name == "Windows":
        font_path = "c:/Windows/Fonts/malgun.ttf"
    elif system_name == "Darwin":
        font_path = "/System/Library/Fonts/AppleGothic.ttf"
    else:
        font_path = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"

    if font_path and Path(font_path).exists():
        return font_path
    return None


def generate_analytics_data():
    reviews = load_json_data(SAVED_REVIEWS_FILE)
    df = pd.DataFrame(reviews)

    if df.empty:
        return pd.DataFrame(), None

    text_corpus = " ".join(df['review_text'].astype(str).tolist())
    if not text_corpus.strip():
        return df, None

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
    """데이터 초기화 (완료된 리뷰 + 임시 저장 데이터 + 커스텀 말투)"""
    print("[INFO] Resetting all data...")

    # 1. 완료된 리뷰 삭제
    save_json_data(SAVED_REVIEWS_FILE, [])

    # 2. [NEW] 작성 중인 임시 데이터 삭제
    save_json_data(DRAFTS_FILE, [])

    # 3. 말투 학습 데이터 초기화 (커스텀만 삭제)
    templates = load_json_data(TEMPLATES_FILE)
    if templates:
        base_templates = [
            t for t in templates
            if t.get("metadata", {}).get("tone") != "owner_custom"
        ]
        if len(templates) != len(base_templates):
            save_json_data(TEMPLATES_FILE, base_templates)

    return True