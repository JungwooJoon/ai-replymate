import os
import json
from langchain_google_genai import ChatGoogleGenerativeAI
from transformers import pipeline
from dotenv import load_dotenv

load_dotenv()

# 전역 변수
sentiment_analyzer = None


def get_llm(model_name="gemini-2.5-flash"):
    """Gemini 모델 인스턴스 반환"""
    llm = ChatGoogleGenerativeAI(
        model=model_name,
        temperature=0.7,
        google_api_key=os.getenv("GOOGLE_API_KEY")
    )
    return llm


def get_sentiment_analyzer():
    global sentiment_analyzer
    if sentiment_analyzer is None:
        print("[INFO] Loading sentiment model...")
        sentiment_analyzer = pipeline(
            "sentiment-analysis",
            model="matthewburke/korean_sentiment"
        )
    return sentiment_analyzer


def analyze_review_sentiment(text):
    """KoBERT 감정 분석"""
    analyzer = get_sentiment_analyzer()
    result = analyzer(text, truncation=True)[0]

    label_map = {"LABEL_0": "negative", "LABEL_1": "positive"}
    mapped_label = label_map.get(result['label'], result['label'])

    return {
        "label": mapped_label,
        "score": round(result['score'], 4)
    }


def auto_classify_reply(reply_text):
    """[Req 4] 사장님 입력 텍스트 분석하여 메타데이터 자동 추출"""
    llm = get_llm()
    prompt = f"""
    Analyze the following restaurant owner's reply and extract metadata in JSON.

    Input Reply: "{reply_text}"

    Requirements:
    1. sentiment: Infer the sentiment of the *original customer review* this reply is addressing (positive or negative).
    2. category: Choose one [taste_good, taste_bad, delivery_delay, wrong_item, quantity, service].

    Output JSON format only:
    {{"sentiment": "...", "category": "..."}}
    """

    try:
        res = llm.invoke(prompt)
        content = res.content.replace("```json", "").replace("```", "").strip()
        return json.loads(content)
    except Exception as e:
        print(f"[ERROR] Auto-classification failed: {e}")
        # 실패 시 기본값 반환
        return {"sentiment": "positive", "category": "service"}