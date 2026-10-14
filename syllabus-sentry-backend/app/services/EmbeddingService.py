from sentence_transformers import SentenceTransformer
class EmbeddingService:
    def __init__(self,model_name: str = "all-MiniLM-L6-v2"):
        self.model=SentenceTransformer(model_name)
    def get_embeddings(self,text:str)->list[float]:
        vector=self.model.encode(text,normalize_embeddings=True)
        return vector.tolist()
    def get_chunk_embeddings(self,texts:list[str])->list[list[float]]:
        vector=self.model.encode(texts,batch_size=32,normalize_embeddings=True)
        return vector.tolist()
    
