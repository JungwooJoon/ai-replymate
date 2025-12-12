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

        # 1. 문서 데이터 준비
        docs = []

        # 템플릿 로드
        templates = self._load_json(template_file)
        for t in templates:
            meta = t.get("metadata", {})
            docs.append(Document(page_content=t["content"], metadata=meta))

        # 메뉴 로드
        menus = self._load_json(menu_file)
        for m in menus:
            content = f"메뉴명: {m['menu_name']} / 특징: {m['description']}"
            meta = {"type": "menu", "name": m['menu_name']}
            docs.append(Document(page_content=content, metadata=meta))

        # 2. DB 업데이트 (삭제 후 재생성 대신 갱신)
        if DB_DIR.exists():
            print("[INFO] Updating existing DB...")
            # 기존 DB 로드
            self.vector_store = Chroma(
                persist_directory=self.persist_dir,
                embedding_function=self.embeddings,
                collection_name="reply_data"
            )

            # [핵심] 기존 데이터 삭제 (IDs 조회 후 삭제)
            # 폴더를 지우는 게 아니라, SQL처럼 데이터만 지움 -> 파일 잠금 안 걸림
            try:
                existing_ids = self.vector_store.get()['ids']
                if existing_ids:
                    self.vector_store.delete(ids=existing_ids)
                    print(f"[INFO] Deleted {len(existing_ids)} old documents.")

                # 새 데이터 추가
                if docs:
                    self.vector_store.add_documents(docs)
                    print(f"[INFO] Added {len(docs)} new documents.")
            except Exception as e:
                print(f"[ERROR] DB update failed: {e}")

        else:
            print("[INFO] Creating new DB...")
            # DB가 아예 없으면 새로 생성
            if docs:
                self.vector_store = Chroma.from_documents(
                    documents=docs,
                    embedding=self.embeddings,
                    persist_directory=self.persist_dir,
                    collection_name="reply_data"
                )

        print(f"[SUCCESS] ChromaDB updated at: {self.persist_dir}")

    def load_db(self):
        self.vector_store = Chroma(
            persist_directory=self.persist_dir,
            embedding_function=self.embeddings,
            collection_name="reply_data"
        )

    def search_templates(self, sentiment: str, category: str = None, tone: str = None, k=2):
        if not self.vector_store:
            self.load_db()

        conditions = [{"sentiment": {"$eq": sentiment}}]

        if category:
            conditions.append({"category": {"$eq": category}})

        if tone:
            conditions.append({"tone": {"$eq": tone}})

        if len(conditions) > 1:
            filter_cond = {"$and": conditions}
        else:
            filter_cond = conditions[0]

        print(f"[INFO] Search Filter: {filter_cond}")

        # 데이터가 없을 경우 에러 방지
        try:
            results = self.vector_store.similarity_search(
                query="리뷰 답변 템플릿",
                k=k,
                filter=filter_cond
            )
            return [doc.page_content for doc in results]
        except Exception as e:
            print(f"[WARN] Search failed (maybe empty DB): {e}")
            return []

    def search_menu(self, query: str, k=1, target_menu_name: str = None):
        """
        메뉴 정보를 가져옵니다.
        target_menu_name이 있으면 유사도 검색 대신 'DB 조회(Exact Match)'를 수행합니다.
        """
        if not self.vector_store:
            self.load_db()

        if target_menu_name and target_menu_name != "null":
            print(f"[INFO] 메뉴 정보 강제 조회 (DB): {target_menu_name}")
            try:
                results = self.vector_store.get(
                    where={"name": target_menu_name},
                    limit=1
                )
                # 조회된 문서가 있으면 반환
                if results['documents']:
                    return results['documents']
            except Exception as e:
                print(f"[WARN] DB Fetch failed: {e}")

            return []

        try:
            results = self.vector_store.similarity_search(
                query=query,
                k=k,
                filter={"type": "menu"}
            )
            return [doc.page_content for doc in results]
        except Exception as e:
            print(f"[WARN] Similarity search failed: {e}")
            return []


if __name__ == "__main__":
    rag = ReplyMateRAG()
    rag.init_db()