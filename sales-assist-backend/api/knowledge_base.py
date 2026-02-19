from fastapi import APIRouter, HTTPException

# NOTE: This module is not registered in main.py.
# Legacy knowledge-base operations are intentionally disabled in this POC.

router = APIRouter()


@router.get("/knowledge-base/stats")
async def get_knowledge_base_stats():
    raise HTTPException(status_code=501, detail="Knowledge base stats not enabled in this POC")


@router.delete("/knowledge-base/clear")
async def clear_knowledge_base():
    raise HTTPException(status_code=501, detail="Knowledge base clear not enabled in this POC")
