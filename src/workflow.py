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
    customer_name: str  # [NEW]
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
    extracted_menu = state.get("extracted_menu")
    if extracted_menu and extracted_menu != "null":
        menu_info = rag.search_menu(query=extracted_menu, k=2)
    else:
        menu_info = rag.search_menu(query=state["review_text"], k=2)

    return {"retrieved_templates": templates, "retrieved_menus": menu_info}


# ------------------------------------------------------------------
# NODE 3: Generate
# ------------------------------------------------------------------
def generate_node(state: GraphState):
    llm = get_llm()

    context_templates = "\n".join([f"- {t}" for t in state["retrieved_templates"]])
    context_menus = "\n".join([f"- {m}" for m in state["retrieved_menus"]])

    feedback_instruction = ""
    if state.get("user_feedback"):
        feedback_instruction = f"""
        [수정 요청] 사용자가 다음 사항을 요구했습니다: "{state['user_feedback']}".
        이 요청을 최우선으로 반영하세요.
        """

    # [NEW] 이름 처리
    cust_name = state.get("customer_name", "").strip()
    if not cust_name: cust_name = "고객"

    system_prompt = f"""
    당신은 식당 사장님입니다. 
    선택된 말투: {state['tone']}
    대상 고객명: {cust_name}

    [가이드라인]
    1. 답글의 시작을 "{cust_name}님"으로 부르며 시작하세요.
    2. 리뷰 감정({state['sentiment']})에 맞춰 대응하세요.
    3. [메뉴 정보]가 있다면 활용하세요.
    4. [추천 템플릿]의 스타일과 어조를 모방하여 답변을 작성하세요.
    {feedback_instruction}

    [추천 템플릿 (말투 참고용)]:
    {context_templates}

    [메뉴 정보]:
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