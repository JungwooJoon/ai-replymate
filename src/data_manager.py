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
DRAFTS_FILE = "draft_reviews.json"
STORE_INFO_FILE = "store_info.json"

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


def save_store_name(name):
    """가게 이름을 JSON 파일에 저장 (딕셔너리 형태)"""
    data = {"store_name": name}
    save_json_data(STORE_INFO_FILE, data)


def load_store_name():
    """저장된 가게 이름 불러오기"""
    # load_json_data는 리스트나 딕셔너리를 반환함
    data = load_json_data(STORE_INFO_FILE)
    if isinstance(data, dict):
        return data.get("store_name", "")
    return


# [FIX] 중복 저장 방지 로직 (ID 기준 덮어쓰기)
def save_completed_review(review_data):
    current_data = load_json_data(SAVED_REVIEWS_FILE)

    # 전달받은 데이터에 ID가 있는지 확인
    target_id = review_data.get("id")

    if target_id:
        # 이미 같은 ID가 있는지 검사
        found_index = -1
        for idx, item in enumerate(current_data):
            if item.get("id") == target_id:
                found_index = idx
                break

        if found_index != -1:
            # 있으면 교체 (Update)
            current_data[found_index] = review_data
            print(f"[INFO] Updated review {target_id}")
        else:
            # 없으면 추가 (Create)
            current_data.append(review_data)
            print(f"[INFO] Created new review {target_id}")
    else:
        # ID가 없으면 그냥 추가 (구형 데이터 호환)
        current_data.append(review_data)

    save_json_data(SAVED_REVIEWS_FILE, current_data)


def save_drafts(draft_data):
    save_json_data(DRAFTS_FILE, draft_data)


def load_drafts():
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
    print("[INFO] Resetting all data...")
    save_json_data(SAVED_REVIEWS_FILE, [])
    save_json_data(DRAFTS_FILE, [])

    templates = load_json_data(TEMPLATES_FILE)
    if templates:
        base_templates = [
            t for t in templates
            if t.get("metadata", {}).get("tone") != "owner_custom"
        ]
        if len(templates) != len(base_templates):
            save_json_data(TEMPLATES_FILE, base_templates)

    return True
