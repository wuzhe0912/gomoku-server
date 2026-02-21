import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.ws_handler import router as ws_router

load_dotenv()

app = FastAPI(title="Gomoku Server")

cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:5174")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in cors_origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(ws_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
