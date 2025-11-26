import os
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

load_dotenv()

def get_llm(model_name="gemini-2.5-flash"):

    llm = ChatGoogleGenerativeAI(
        model=model_name,
        temperature=0.7,
        google_api_key=os.getenv("GOOGLE_API_KEY")
    )
    return llm

# 테스트 코드
if __name__ == "__main__":
    llm = get_llm()
    response = llm.invoke("안녕하세요, 사장님 톤으로 인사 한번 해주세요.")
    print(response.content)