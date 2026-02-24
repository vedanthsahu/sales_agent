from __future__ import annotations

from datetime import datetime
import uuid
from typing import Any, Dict, List, Optional

from bson import ObjectId

from logger import enhanced_logger
from utils.database import get_database


def _to_object_id(file_id: str) -> ObjectId:
    try:
        return ObjectId(file_id)
    except Exception as exc:
        raise ValueError(f"Invalid file_id: {file_id}") from exc


def get_db():
    return get_database()


async def ensure_indexes() -> None:
    db = get_db()
    await db["chat_history"].create_index([("session_id", 1), ("domain", 1)])
    await db["sessions"].create_index([("user_id", 1), ("is_active", 1)])


async def insert_file_metadata(
    filename: str,
    content_type: str,
    domain: str,
    file_path: Optional[str] = None,
    file_hash: Optional[str] = None,
) -> str:
    db = get_db()
    doc: Dict[str, Any] = {
        "filename": filename,
        "content_type": content_type,
        "domain": domain,
        "created_at": datetime.utcnow(),
        "processing_status": "uploaded",
    }
    if file_path:
        doc["file_path"] = file_path
    if file_hash:
        doc["file_hash"] = file_hash

    result = await db["files"].insert_one(doc)
    return str(result.inserted_id)


async def update_file_status(
    file_id: str,
    status: str,
    extra_fields: Optional[Dict[str, Any]] = None,
) -> None:
    db = get_db()
    update_doc: Dict[str, Any] = {
        "processing_status": status,
        "updated_at": datetime.utcnow(),
    }
    if extra_fields:
        update_doc.update(extra_fields)

    await db["files"].update_one(
        {"_id": _to_object_id(file_id)},
        {"$set": update_doc},
    )


async def get_file(file_id: str) -> Optional[Dict[str, Any]]:
    db = get_db()
    return await db["files"].find_one({"_id": _to_object_id(file_id)})


async def insert_chunks(chunk_docs: List[Dict[str, Any]]) -> None:
    if not chunk_docs:
        return
    db = get_db()
    await db["chunks"].insert_many(chunk_docs)
    enhanced_logger.debug(
        "MONGO_CHUNKS_INSERTED",
        extra_data={"count": len(chunk_docs)},
    )


async def delete_chunks_for_file(file_id: str) -> int:
    db = get_db()
    result = await db["chunks"].delete_many({"file_id": file_id})
    return int(result.deleted_count)


async def count_chunks_for_file(file_id: str) -> int:
    db = get_db()
    return await db["chunks"].count_documents({"file_id": file_id})


async def get_chunks_by_ids(chunk_ids: List[str]) -> Dict[str, Dict[str, Any]]:
    if not chunk_ids:
        return {}
    db = get_db()
    cursor = db["chunks"].find({"chunk_id": {"$in": chunk_ids}})
    results: Dict[str, Dict[str, Any]] = {}
    async for doc in cursor:
        results[doc["chunk_id"]] = doc
    return results


async def list_files(domain: Optional[str] = None) -> List[Dict[str, Any]]:
    db = get_db()
    query: Dict[str, Any] = {}
    if domain:
        query["domain"] = domain
    cursor = db["files"].find(query).sort("created_at", -1)
    results: List[Dict[str, Any]] = []
    async for doc in cursor:
        results.append(
            {
                "file_id": str(doc["_id"]),
                "filename": doc.get("filename"),
                "created_at": doc.get("created_at"),
                "processing_status": doc.get("processing_status"),
                "domain": doc.get("domain"),
            }
        )
    return results


async def find_file_by_hash(file_hash: str, domain: Optional[str] = None) -> Optional[Dict[str, Any]]:
    db = get_db()
    query: Dict[str, Any] = {"file_hash": file_hash}
    if domain:
        query["domain"] = domain
    return await db["files"].find_one(query)


async def create_session(user_id: str) -> str:
    db = get_db()
    session_id = uuid.uuid4().hex
    await db["sessions"].insert_one(
        {
            "session_id": session_id,
            "user_id": user_id,
            "created_at": datetime.utcnow(),
            "is_active": True,
        }
    )
    return session_id


async def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    db = get_db()
    return await db["sessions"].find_one({"session_id": session_id})


async def end_session(session_id: str) -> None:
    db = get_db()
    await db["sessions"].update_one(
        {"session_id": session_id},
        {"$set": {"is_active": False, "ended_at": datetime.utcnow()}},
    )


async def append_chat_messages(
    session_id: str,
    domain: str,
    messages: List[Dict[str, Any]],
) -> None:
    if not messages:
        return
    db = get_db()
    await db["chat_history"].update_one(
        {"session_id": session_id, "domain": domain},
        {
            "$setOnInsert": {"created_at": datetime.utcnow()},
            "$set": {"updated_at": datetime.utcnow()},
            "$push": {"messages": {"$each": messages}},
        },
        upsert=True,
    )


async def get_chat_history(session_id: str, domain: str) -> List[Dict[str, Any]]:
    db = get_db()
    doc = await db["chat_history"].find_one(
        {"session_id": session_id, "domain": domain}
    )
    if not doc:
        return []
    return list(doc.get("messages") or [])
