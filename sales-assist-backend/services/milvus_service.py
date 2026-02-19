from __future__ import annotations

import os
from typing import Dict, List, Sequence

from pymilvus import (
    Collection,
    CollectionSchema,
    DataType,
    FieldSchema,
    connections,
    utility,
)

from logger import enhanced_logger


_connected = False
_collection: Collection | None = None


def _connect() -> None:
    global _connected
    if _connected:
        return

    connections.connect(
        alias="default",
        host=os.getenv("MILVUS_HOST"),
        port=os.getenv("MILVUS_PORT"),
    )
    _connected = True


def _get_collection_name() -> str:
    name = os.getenv("MILVUS_COLLECTION", "sales_assist_embeddings")
    return name


def _ensure_collection() -> Collection:
    global _collection
    if _collection is not None:
        return _collection

    _connect()

    collection_name = _get_collection_name()
    dim = int(os.getenv("MILVUS_DIMENSION", "384"))

    if not utility.has_collection(collection_name):
        fields = [
            FieldSchema(
                name="id",
                dtype=DataType.VARCHAR,
                is_primary=True,
                max_length=128,
            ),
            FieldSchema(
                name="embedding",
                dtype=DataType.FLOAT_VECTOR,
                dim=dim,
            ),
            FieldSchema(
                name="file_id",
                dtype=DataType.VARCHAR,
                max_length=128,
            ),
            FieldSchema(
                name="domain",
                dtype=DataType.VARCHAR,
                max_length=64,
            ),
            FieldSchema(
                name="chunk_index",
                dtype=DataType.INT64,
            ),
        ]
        schema = CollectionSchema(
            fields=fields,
            description="Sales Assist embeddings",
        )
        _collection = Collection(name=collection_name, schema=schema)
        _collection.create_index(
            field_name="embedding",
            index_params={
                "index_type": "IVF_FLAT",
                "metric_type": "IP",
                "params": {"nlist": 1024},
            },
        )
        enhanced_logger.info(
            "MILVUS_COLLECTION_CREATED",
            extra_data={"collection": collection_name, "dimension": dim},
        )
    else:
        _collection = Collection(collection_name)
        # Validate embedding dimension matches expected env
        try:
            embedding_field = next(
                (field for field in _collection.schema.fields if field.name == "embedding"),
                None,
            )
            if embedding_field is not None:
                existing_dim = None
                if hasattr(embedding_field, "params") and embedding_field.params:
                    existing_dim = embedding_field.params.get("dim")
                if existing_dim is None and hasattr(embedding_field, "dim"):
                    existing_dim = embedding_field.dim
                if existing_dim is not None and int(existing_dim) != dim:
                    raise RuntimeError(
                        f"Milvus collection dimension mismatch: expected {dim}, found {existing_dim}"
                    )
        except Exception as exc:
            raise RuntimeError(
                f"Milvus collection dimension validation failed: {exc}"
            ) from exc

    _collection.load()
    return _collection


def init_milvus() -> None:
    """
    Initialize Milvus connection and ensure collection exists.
    Intended to be called on application startup.
    """
    _ensure_collection()


def insert_embeddings(
    ids: Sequence[str],
    embeddings: Sequence[Sequence[float]],
    metadata: Sequence[Dict[str, object]],
    batch_size: int = 128,
) -> None:
    if not ids:
        return
    if not (len(ids) == len(embeddings) == len(metadata)):
        raise ValueError("ids, embeddings, and metadata must be the same length")

    collection = _ensure_collection()

    for start in range(0, len(ids), batch_size):
        end = start + batch_size
        batch_ids = ids[start:end]
        batch_embeddings = embeddings[start:end]
        batch_meta = metadata[start:end]

        file_ids = [m["file_id"] for m in batch_meta]
        domains = [m["domain"] for m in batch_meta]
        chunk_indices = [m["chunk_index"] for m in batch_meta]

        entities = [
            list(batch_ids),
            list(batch_embeddings),
            file_ids,
            domains,
            chunk_indices,
        ]
        collection.insert(entities)


def delete_embeddings_by_file_id(file_id: str) -> None:
    collection = _ensure_collection()
    expr = f'file_id == "{file_id}"'
    collection.delete(expr)


def search_embeddings(
    query_embedding: List[float],
    top_k: int,
    file_ids: List[str] | None = None,
    domain: str | None = None,
):
    collection = _ensure_collection()

    expr_parts = []
    if file_ids:
        quoted = [f'"{fid}"' for fid in file_ids]
        expr_parts.append(f"file_id in [{', '.join(quoted)}]")
    if domain:
        expr_parts.append(f'domain == "{domain}"')

    expr = " and ".join(expr_parts) if expr_parts else None

    results = collection.search(
        data=[query_embedding],
        anns_field="embedding",
        param={"metric_type": "IP", "params": {"nprobe": 10}},
        limit=top_k,
        expr=expr,
        output_fields=["id", "file_id", "chunk_index", "domain"],
    )
    return results[0]
