from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
import json

# Load env once
load_dotenv()

# Routers
from api.ask import router as chat_router
from api.upload import router as upload_router
from api.files import router as files_router
from api.session import router as session_router
from services.milvus_service import init_milvus
from services.mongo_service import ensure_indexes

app = FastAPI(title="Sales Assist Backend")

# CORS (Vite dev server)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def domain_required_middleware(request: Request, call_next):
    if request.url.path == "/chat" and request.method.upper() == "POST":
        try:
            raw_body = await request.body()
            if not raw_body:
                return JSONResponse(status_code=400, content={"detail": "Domain required"})
            payload = json.loads(raw_body)
            if not payload.get("domain"):
                return JSONResponse(status_code=400, content={"detail": "Domain required"})
            request._body = raw_body
        except Exception:
            return JSONResponse(status_code=400, content={"detail": "Domain required"})
    return await call_next(request)

# Mount routers
app.include_router(chat_router, tags=["chat"])
app.include_router(upload_router, tags=["files"])
app.include_router(files_router, tags=["files"])
app.include_router(session_router, tags=["sessions"])


@app.on_event("startup")
async def _startup():
    init_milvus()
    await ensure_indexes()


@app.get("/health")
async def health():
    return {"status": "ok"}
