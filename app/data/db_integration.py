import chromadb
from chromadb.utils import embedding_functions
from app.core.config import STORAGE_PATH

if STORAGE_PATH is None:
    raise ValueError("DB Storage path is wrong!!")

class DB_Controller:
    def __init__(self, openai_api_key, storage_path):
        self.db_client = chromadb.PersistentClient(storage_path)
        self.openai_ef = embedding_functions.OpenAIEmbeddingFunction(
            model_name="text-embedding-ada-002",
            api_key=openai_api_key
        )
        
        self.collection = self.db_client.get_or_create_collection(name="products_db", embedding_function=self.openai_ef)

    def load_collection(self):
        return self.collection

    def create_collection(self, documents, ids, metadatas):
        if self.collection.count() == 0:
            print("Collection is empty, Filling with Data form JSON...")
            tea_embeddings = self.openai_ef(documents)
            self.collection.add(
                embeddings=tea_embeddings,
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            print("Collection created Successfully!")
        else:
            print("Collection already ready!")
        
        return self.collection
    
    def query_new(self, query_text: str, n_results: int = 10, where: dict | None = None):       # change to this function in the future
        if not where:
            where = None

        return self.collection.query(
            query_texts=[query_text],
            n_results=n_results,
            where=where
        )