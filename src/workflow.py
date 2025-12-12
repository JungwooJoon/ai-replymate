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
    """
    RAG 검색 노드 (메뉴 정보 및 말투 템플릿 검색)
    """
    print("--- RETRIEVE INFO ---")
    rag = ReplyMateRAG()

    # 1. 타겟 메뉴명 확인 (UI 선택값 우선 -> 없으면 AI 추출값)
    target_menu = state.get("manual_menu")
    if not target_menu or target_menu == "null":
        target_menu = state.get("extracted_menu")

    print(f"검색 대상 메뉴: {target_menu}")  # 로그 확인용

    # 2. [핵심] 수정된 search_menu 함수 호출 (target_menu_name 인자 전달)
    # 이제 유사도 검색이 아니라 'DB 직접 조회'를 수행합니다.
    menu_docs = rag.search_menu(state["review_text"], target_menu_name=target_menu)

    # 3. 말투 템플릿 검색
    tone_docs = rag.search_templates(
        state["sentiment"],
        # 카테고리나 톤 정보가 있으면 추가 필터링 가능 (여기서는 기본 검색)
    )

    # 검색 결과 로그 출력
    print(f"검색된 메뉴 정보: {menu_docs}")
    print(f"검색된 말투 예시: {len(tone_docs)}개")

    return {
        "retrieved_menus": menu_docs,
        "retrieved_templates": tone_docs
    }


# ------------------------------------------------------------------
# NODE 3: Generate
# ------------------------------------------------------------------
def generate_node(state: GraphState):
    llm = get_llm()

    # ------------------------------------------------------------------
    # 1. 데이터 전처리 (리스트 -> 문자열 변환)
    # ------------------------------------------------------------------
    if state["retrieved_templates"]:
        context_templates = "\n".join([f"- {t}" for t in state["retrieved_templates"]])
    else:
        context_templates = "참고할 템플릿이 없습니다."

    if state["retrieved_menus"]:
        context_menus = "\n".join([f"- {m}" for m in state["retrieved_menus"]])
    else:
        context_menus = "None"

    # ------------------------------------------------------------------
    # 2. 톤(Tone)에 따른 프롬프트 지시사항 분기 (핵심 로직)
    # ------------------------------------------------------------------
    current_tone = state.get("tone", "친근한")

    if current_tone == "정중한":
        # [A] 정중한 모드: 이모티콘 금지, 격식체 강제
        tone_instructions = """
        3. **Tone & Manner (FORMAL MODE):**
           - **STRICTLY FORBIDDEN:** Do NOT use emojis (e.g., ^^, ㅠㅠ, 😊) and Tildes (~).
           - **Style:** Professional, Objective, and Polite (Like a Hotel Concierge).
           - **Endings:** Use formal endings like "~입니다", "~하겠습니다", "~십시오".
           - **Structure:** Start with "고객님," or "{state['customer_name']}님,".
        """
    else:
        # [B] 사장님/친근한 모드: 데이터 모방, 텍스트 이모티콘 허용
        tone_instructions = """
        3. **Tone & Manner (OWNER/CASUAL MODE):**
           - **Style Source:** Mimic 'Owner's Tone Examples' (BELOW) exactly.
           - **Emojis:** Use text emojis (^^, ㅠㅠ) and Tildes (~) naturally as seen in examples.
           - **Endings:** Use soft endings like "~요", "~네요", "~답니다".
           - **Length:** Keep it short and friendly.
        """

    # ------------------------------------------------------------------
    # 3. 시스템 프롬프트 조립
    # ------------------------------------------------------------------
    system_prompt = f"""
    You are the owner of the restaurant '{state.get("store_name", "우리 가게")}'.
    Reply to the customer's review.

    [Sources]
    - **Content Source:** Use 'Matched Menu Info' (BELOW) for the solution.
    - **Style Source:** Follow the 'Tone & Manner' instructions below.

    [Context Information]
    1. **Customer Name:** {state['customer_name']}
    2. **Matched Menu Info:** {context_menus}
    3. **Owner's Tone Examples:** {context_templates}

    [Critical Instructions]
    1. **Smart Addressing (CRITICAL):**
       - **NEVER output "OO님" literally.** You must replace "OO" with the actual customer name.
       - **Step 1:** Look at [Context Information] > 'Customer Name'.
       - **Step 2:** Decide how to call them:
         - **Case A (Normal Name/ID):** If it looks like a name (e.g., "홍길동", "minji99"), say **"{state['customer_name']}님!"** or **"{state['customer_name']}님 안녕하세요 ^^"**.
         - **Case B (Awkward/Long Nickname):** If it is a phrase or awkward (e.g., "매일먹는사람", "맛있으면짖는개"), **IGNORE the name** and use **"고객님"** or **"단골님"**.
       - **Example:** - Name="이정우" -> "**이정우님** 안녕하세요 ^^" (Good)
         - Name="매일먹는사람" -> "**단골님** 안녕하세요 ^^" (Good)
         - Name="매일먹는사람" -> "매일먹는사람님 안녕하세요" (BAD)

    2. **PRIORITY 1: The Solution (From Menu Info)**
       - Does 'Matched Menu Info' contain a specific tip?
       - **Relevance Check:** Does the customer's review mention this menu? Or is this menu selected?
       - **IF RELEVANT:** You MUST write the tip (e.g., "전자레인지 30초").
       - **IF IRRELEVANT:** Do NOT mention it.

    {tone_instructions}

    4. **Structure:**
       - **Greeting:** Smart Address + Hello.
       - **Empathy:** Brief thanks or apology.
       - **Closing:** Friendly closing.

    5. **User Feedback:**
       {state.get('user_feedback', 'None')}
    """

    user_prompt = f"고객 리뷰: {state['review_text']}"

    # ------------------------------------------------------------------
    # 4. 모델 호출 및 결과 반환
    # ------------------------------------------------------------------
    res = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ])

    return {
        "final_reply": res.content,
        "sentiment": state.get("sentiment", "unknown")
    }


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