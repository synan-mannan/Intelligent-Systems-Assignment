from functools import lru_cache

from langchain_chroma import Chroma

from app.rag.ingestion import create_vector_store


@lru_cache(maxsize=1)
def get_vector_store() -> Chroma:
    return create_vector_store()


def retrieve_handbook_context(question: str) -> list:
    return get_vector_store().similarity_search(question, k=4)