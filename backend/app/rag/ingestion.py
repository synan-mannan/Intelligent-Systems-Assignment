from pathlib import Path
from urllib.request import urlretrieve

from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

PDF_URL = "https://raw.githubusercontent.com/Azure-Samples/azure-search-openai-demo/main/data/employee_handbook.pdf"
DATA_DIR = Path(__file__).resolve().parents[2] / "data"
PDF_PATH = DATA_DIR / "employee_handbook.pdf"
CHROMA_DIR = DATA_DIR / "chroma"
COLLECTION_NAME = "employee-handbook"


def create_vector_store() -> Chroma:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not PDF_PATH.exists():
        urlretrieve(PDF_URL, PDF_PATH)

    store = Chroma(
        collection_name=COLLECTION_NAME,
        persist_directory=str(CHROMA_DIR),
        embedding_function=None,
    )
    if store._collection.count() == 0:
        pages = PyPDFLoader(str(PDF_PATH)).load()
        chunks = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=150,
        ).split_documents(pages)
        store.add_documents(chunks)
    return store