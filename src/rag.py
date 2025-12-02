# ... (기존 import 및 init 부분 동일) ...
import json
import shutil
from pathlib import Path
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_DIR = BASE_DIR / "chroma_db"


class ReplyMateRAG:
    def __init__(self):
        self.persist_dir = str(DB_DIR)
        self.embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
        self.vector_store = None

    def _load_json(self, filename):
        file_path = DATA_DIR / filename
        if not file_path.exists():
            print(f"[WARN] File not found: {file_path}")
            return []
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def init_db(self, template_file="templates.json", menu_file="menu_info.json"):
        if DB_DIR.exists():
            shutil.rmtree(DB_DIR)

        templates = self._load_json(template_file)
        docs = []
        for t in templates:
            # 메타데이터가 없는 경우 대비
            meta = t.get("metadata", {})
            docs.append(Document(page_content=t["content"], metadata=meta))

        menus = self._load_json(menu_file)
        for m in menus:
            content = f"메뉴명: {m['menu_name']} / 특징: {m['description']}"
            meta = {"type": "menu", "name": m['menu_name']}
            docs.append(Document(page_content=content, metadata=meta))

        self.vector_store = Chroma.from_documents(
            documents=docs,
            embedding=self.embeddings,
            persist_directory=self.persist_dir,
            collection_name="reply_data"
        )
        print(f"[SUCCESS] ChromaDB initialized at: {self.persist_dir}")

    def load_db(self):
        if not Path(self.persist_dir).exists() or not any(Path(self.persist_dir).iterdir()):
            print("[INFO] DB not found on server. Initializing automatically...")
            self.init_db()

        self.vector_store = Chroma(
            persist_directory=self.persist_dir,
            embedding_function=self.embeddings,
            collection_name="reply_data"
        )

    def search_templates(self, sentiment: str, category: str = None, tone: str = None, k=2):
        if not self.vector_store:
            self.load_db()

        conditions = []

        # 1. sentiment는 필수 값이므로 항상 추가 (None이면 에러 발생 가능성 있으므로 체크)
        if sentiment:
            conditions.append({"sentiment": {"$eq": sentiment}})

        # 2. category가 유효한 값(None이 아니고 빈 문자열 아님)일 때만 추가
        if category and category != "null":
            conditions.append({"category": {"$eq": category}})

        # 3. tone이 유효한 값일 때만 추가
        if tone:
            conditions.append({"tone": {"$eq": tone}})

        # 조건 조합 로직
        if len(conditions) > 1:
            filter_cond = {"$and": conditions}
        elif len(conditions) == 1:
            filter_cond = conditions[0]
        else:
            # 조건이 하나도 없으면 필터링 없이 검색 (또는 빈 딕셔너리)
            filter_cond = {}

        print(f"[INFO] Search Filter: {filter_cond}")

        try:
            results = self.vector_store.similarity_search(
                query="리뷰 답변 템플릿",
                k=k,
                filter=filter_cond if filter_cond else None  # 필터가 비었으면 None 전달
            )
            return [doc.page_content for doc in results]
        except Exception as e:
            print(f"[WARN] Search failed: {e}")
            return []

    def search_menu(self, query: str, k=1):
        if not query or not isinstance(query, str):
            return []

        if not self.vector_store:
            self.load_db()

        try:
            results_with_score = self.vector_store.similarity_search_with_score(
                query=query,
                k=k,
                filter={"type": "menu"}
            )

            valid_docs = []
            for doc, score in results_with_score:
                if score < 0.8:
                    valid_docs.append(doc.page_content)
                else:
                    print(f"[INFO] Menu dropped due to low similarity: {doc.page_content} (Score: {score})")

            return valid_docs

        except Exception as e:
            print(f"[WARN] Menu search failed: {e}")
            return []


if __name__ == "__main__":
    rag = ReplyMateRAG()
    rag.init_db()