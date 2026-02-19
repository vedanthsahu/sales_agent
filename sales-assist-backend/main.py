from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load env once
load_dotenv()

# Routers
from api.ask import router as chat_router
from api.upload import router as upload_router
from api.files import router as files_router
from services.milvus_service import init_milvus

app = FastAPI(title="Sales Assist Backend")

# CORS (Vite dev server)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers
app.include_router(chat_router, tags=["chat"])
app.include_router(upload_router, tags=["files"])
app.include_router(files_router, tags=["files"])


@app.on_event("startup")
async def _startup():
    init_milvus()


@app.get("/health")
async def health():
    return {"status": "ok"}
