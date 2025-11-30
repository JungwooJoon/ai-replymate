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

    # 감정 분석
    sentiment_result = analyze_review_sentiment(review)
    sentiment = sentiment_result["label"]

    # 카테고리/메뉴 추출 (LLM)
    llm = get_llm()
    prompt = f"""
    Analyze review. Extract JSON:
    - category: [taste, delivery, service, quantity, wrong_item]
    - menu: food name or "null"

    Review: {review}
    JSON Output:
    """
    try:
        res = llm.invoke(prompt)
        content = res.content.replace("```json", "").replace("```", "").strip()
        import json
        data = json.loads(content)
        category = data.get("category", "service")
        menu = data.get("menu", "null")
    except:
        category = "service"
        menu = "null"

    print(f"[INFO] Analyze: {sentiment}, {category}, {menu}")
    return {"sentiment": sentiment, "category": category, "extracted_menu": menu}


# ------------------------------------------------------------------
# NODE 2: Retrieve
# ------------------------------------------------------------------
def retrieve_node(state: GraphState):
    tone = state["tone"]

    # [Req 1] 톤 필터링 로직 변경
    # "사장님 말투"가 선택되면 tone="owner_custom"으로 필터링
    # 그 외(정중, 친근, 유머)는 선택된 값 그대로 사용
    target_tone = "owner_custom" if tone == "사장님 말투" else tone_map.get(tone, "polite")

    # 톤 매핑 (한글 UI -> 영어 메타데이터)
    # UI에서 "정중한", "친근한" 등으로 넘어오므로 변환 필요
    # 단, "사장님 말투"는 위에서 처리됨

    templates = rag.search_templates(
        sentiment=state["sentiment"],
        category=state["category"],
        tone=target_tone,  # RAG 메서드에 tone 인자 추가 필요 (아래 rag.py 수정 참고)
        k=3
    )

    menu_info = []
    if state["extracted_menu"] != "null":
        menu_info = rag.search_menu(query=state["extracted_menu"], k=2)
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

    system_prompt = f"""
    당신은 식당 사장님입니다. 
    선택된 말투: {state['tone']}

    [가이드라인]
    1. 리뷰 감정({state['sentiment']})에 맞춰 대응하세요.
    2. [메뉴 정보]가 있다면 활용하세요.
    3. [추천 템플릿]의 스타일과 어조를 모방하여 답변을 작성하세요.
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


# 톤 매핑 딕셔너리
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