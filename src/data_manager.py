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
    print(f"[INFO] Data saved to {filename}")


def save_completed_review(review_data):
    current_data = load_json_data(SAVED_REVIEWS_FILE)
    current_data.append(review_data)
    save_json_data(SAVED_REVIEWS_FILE, current_data)


def get_korean_font_path():
    """OS별 한글 폰트 경로 확인"""
    system_name = platform.system()
    font_path = None

    if system_name == "Windows":
        font_path = "c:/Windows/Fonts/malgun.ttf"
    elif system_name == "Darwin":
        font_path = "/System/Library/Fonts/AppleGothic.ttf"
    else:
        # 리눅스 (Streamlit Cloud 등)
        font_path = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"

    # 폰트 파일 존재 여부 확인
    if font_path and Path(font_path).exists():
        return font_path
    else:
        print(f"[WARN] Font not found at {font_path}. Using default font.")
        return None


def generate_analytics_data():
    reviews = load_json_data(SAVED_REVIEWS_FILE)
    df = pd.DataFrame(reviews)

    if df.empty:
        return pd.DataFrame(), None

    # 워드클라우드 생성
    text_corpus = " ".join(df['review_text'].astype(str).tolist())

    # 텍스트가 비어있으면 조기 리턴
    if not text_corpus.strip():
        return df, None

    font_path = get_korean_font_path()

    try:
        # font_path가 None이면 기본 폰트 사용 (한글 깨짐 가능성 있음)
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
    print("[INFO] Resetting saved reviews...")
    save_json_data(SAVED_REVIEWS_FILE, [])

    templates = load_json_data(TEMPLATES_FILE)
    if templates:
        base_templates = [
            t for t in templates
            if t.get("metadata", {}).get("tone") != "owner_custom"
        ]

        if len(templates) != len(base_templates):
            save_json_data(TEMPLATES_FILE, base_templates)
            print(f"[INFO] Removed {len(templates) - len(base_templates)} custom templates.")
        else:
            print("[INFO] No custom templates to remove.")

    return True