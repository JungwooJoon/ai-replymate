import operator
from typing import Annotated, TypedDict, List
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, END, START

from src.models import analyze_review_sentiment, get_llm
from src.rag import ReplyMateRAG

# RAG 초기화
rag = ReplyMateRAG()


class GraphState(TypedDict):
    review_text: str
    customer_name: str
    manual_menu: str
    store_name: str
    sentiment: str
    category: str
    extracted_menu: str
    tone: str
    retrieved_templates: List[str]
    retrieved_menus: List[str]
    final_reply: str
    user_feedback: str


# ------------------------------------------------------------------
# NODE 1: Analyze
# ------------------------------------------------------------------
def analyze_node(state: GraphState):
    review = state["review_text"]
    cust_name = state.get("customer_name", "")

    # 1. KoBERT 1차 분석 (기계적 분석)
    # KoBERT는 텍스트 자체의 분위기만 봅니다.
    kobert_result = analyze_review_sentiment(review)
    initial_sentiment = kobert_result["label"]

    # 2. LLM 2차 분석 (맥락 및 키워드 추출)
    # [핵심] 고객 닉네임과 리뷰의 관계를 파악하도록 지시
    llm = get_llm()

    # 프롬프트: 닉네임의 컨셉을 이해하라고 구체적으로 지시
    prompt = f"""
    Analyze the review considering the customer's nickname context.

    Customer Name: "{cust_name}"
    Review Text: "{review}"
    KoBERT Analysis: {initial_sentiment}

    Task:
    1. Extract category (taste, delivery, service, quantity, wrong_item).
    2. Extract menu name (or "null").
    3. **Determine Final Sentiment (Crucial):**
       - **Check the Nickname:** Does the nickname imply a specific action for good food? (e.g., "맛있으면 짖는 개" -> implies barking "멍멍" means delicious).
       - **Context Match:** If the review text matches the nickname's condition, override KoBERT and mark it as **"positive"** (Extreme Praise).
       - Otherwise, follow standard sentiment analysis.

    JSON Output format:
    {{
        "category": "...",
        "menu": "...",
        "final_sentiment": "positive" or "negative"
    }}
    """

    try:
        res = llm.invoke(prompt)
        content = res.content.replace("```json", "").replace("```", "").strip()
        import json
        data = json.loads(content)

        category = data.get("category", "service")
        menu = data.get("menu", "null")
        sentiment = data.get("final_sentiment", initial_sentiment)  # LLM의 판단을 최우선으로 함

        # 디버깅용 로그
        if sentiment != initial_sentiment:
            print(f"[INFO] Sentiment Overridden by LLM: {initial_sentiment} -> {sentiment} (Reason: Context)")

    except Exception as e:
        print(f"[WARN] LLM Analysis failed: {e}")
        category = "service"
        menu = "null"
        sentiment = initial_sentiment  # 실패 시 KoBERT 결과 사용

    print(f"[INFO] Analyze Result: {sentiment}, {category}, {menu}")

    return {
        "sentiment": sentiment,
        "category": category,
        "extracted_menu": menu
    }


# ------------------------------------------------------------------
# NODE 2: Retrieve
# ------------------------------------------------------------------
def retrieve_node(state: GraphState):
    tone = state["tone"]
    target_tone = "owner_custom" if tone == "사장님 말투" else tone_map.get(tone, "polite")

    templates = rag.search_templates(
        sentiment=state["sentiment"],
        category=state["category"],
        tone=target_tone,
        k=3
    )

    menu_info = []

    # [LOGIC] 사용자가 직접 입력한 메뉴가 있으면 최우선 사용
    manual_menu = state.get("manual_menu", "").strip()
    extracted_menu = state.get("extracted_menu", "")

    target_query = ""

    if manual_menu:
        print(f"[INFO] Using manual menu: {manual_menu}")
        target_query = manual_menu
    elif extracted_menu and extracted_menu != "null":
        print(f"[INFO] Using extracted menu: {extracted_menu}")
        target_query = extracted_menu
    else:
        print(f"[INFO] Using full review text for search")
        target_query = state["review_text"]

    # 메뉴 검색 실행
    if target_query:
        menu_info = rag.search_menu(query=target_query, k=2)

    return {"retrieved_templates": templates, "retrieved_menus": menu_info}


# ------------------------------------------------------------------
# NODE 3: Generate
# ------------------------------------------------------------------
def generate_node(state: GraphState):
    llm = get_llm()

    # 템플릿이 리스트로 들어오므로 문자열로 변환
    if state["retrieved_templates"]:
        context_templates = "\n".join([f"- {t}" for t in state["retrieved_templates"]])
    else:
        context_templates = "참고할 템플릿이 없습니다. 일반적인 정중한 말투로 작성하세요."

    # 메뉴 정보 처리
    context_menus = ""
    if state["retrieved_menus"]:
        context_menus = "\n".join([f"- {m}" for m in state["retrieved_menus"]])

    # 사용자 피드백 처리
    feedback_instruction = ""
    if state.get("user_feedback"):
        feedback_instruction = f"""
        [수정 요청] 사용자가 다음 사항을 요구했습니다: "{state['user_feedback']}".
        이 요청을 최우선으로 반영하세요.
        """

    cust_name = state.get("customer_name", "").strip()
    if not cust_name: cust_name = "고객"

    store_name = state.get("store_name", "").strip()
    store_identity = f"당신은 '{store_name}' 사장님입니다." if store_name else "당신은 식당 사장님입니다."

    # [FIX] 프롬프트 대폭 수정: 스타일 모방 강제
    system_prompt = f"""
    {store_identity}

    너의 임무는 아래 [추천 템플릿]의 말투를 **'완벽하게 복제'**하여 답글을 다는 것이다.

    [대상 정보]
    - 고객명: {cust_name}
    - 감정: {state['sentiment']}

    [강력한 스타일 가이드 - 반드시 지킬 것]
    1. **길이 제한:** [추천 템플릿]과 비슷한 길이(1~3문장)로 짧게 작성해. 절대 길게 쓰지 마.
    2. **말투 복제:** 템플릿에 있는 문체, 종결어미, 이모티콘(예: ^^, ㅠㅠ, !) 사용 빈도를 그대로 따라해.
    3. **미사여구 금지:** "따뜻한 칭찬", "보람을 느낍니다" 같은 느끼하고 오글거리는 AI식 표현 절대 금지.
    4. **형식:** 서론-본론-결론 형식을 버리고, 템플릿처럼 용건만 간단히 말해.
    5. **가게 이름:** 자연스러울 때만 짧게 언급해.

    {feedback_instruction}

    [추천 템플릿 (이 말투를 그대로 베껴라)]:
    {context_templates}

    [메뉴 정보 (필요시 참고)]:
    {context_menus}
    """

    user_prompt = f"고객 리뷰: {state['review_text']}"

    res = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ])

    return {"final_reply": res.content}


tone_map = {
    "정중한": "polite",
    "친근한": "friendly",
    "유머러스한": "witty"
}


def build_graph():
    workflow = StateGraph(GraphState)
    workflow.add_node("analyze", analyze_node)
    workflow.add_node("retrieve", retrieve_node)
    workflow.add_node("generate", generate_node)

    workflow.add_edge(START, "analyze")
    workflow.add_edge("analyze", "retrieve")
    workflow.add_edge("retrieve", "generate")
    workflow.add_edge("generate", END)

    return workflow.compile()