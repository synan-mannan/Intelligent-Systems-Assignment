import asyncio
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.rag.retriever import get_vector_store

load_dotenv()


@asynccontextmanager
async def lifespan(_: FastAPI):
    await asyncio.to_thread(get_vector_store)
    yield


app = FastAPI(title="People Operations Assistant", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
app.include_router(router)