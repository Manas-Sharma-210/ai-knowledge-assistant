from sentence_transformers import SentenceTransformer

class EmbeddingModel:
    def __init__(self):
        self.model =  SentenceTransformer("all-MiniLM-L6-v2")

    def embed_texts(self, texts:list[str])->list[list[float]]:
          """
        Convert text chunks into vector embeddings
        """

          embeddings = self.model.encode(texts)
          return embeddings.tolist()    
