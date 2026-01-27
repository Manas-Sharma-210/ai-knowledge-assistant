import chromadb
from chromadb.config import Settings

class VectorStore:
    def __init__(self, persist_directory: str = "app/data/chroma"):
        self.client = chromadb.Client(
            Settings(
                persist_directory=persist_directory,
                anonymized_telemetry=False
            )
        )

        self.collection = self.client.get_or_create_collection(
            name="documents"
        )

    def add_documents(self, texts: list[str], embeddings: list[list[float]]):
        ids = [f"doc_{i}" for i in range(len(texts))]

        self.collection.add(
            documents=texts,
            embeddings=embeddings,
            ids=ids
        )

    def search(self, query_embedding: list[float], top_k: int = 5):
        return self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )

    def search_all(self, limit: int = 20):
        results = self.collection.get(include=["documents"])
        docs = [
            doc for doc in results["documents"]
            if doc and isinstance(doc, str) and doc.strip()
        ]
        return docs[:limit]

    # ✅ THIS MUST BE INSIDE THE CLASS
    def reset(self):
        self.client.delete_collection(name="documents")
        self.collection = self.client.get_or_create_collection(
            name="documents"
        )

  

    
    