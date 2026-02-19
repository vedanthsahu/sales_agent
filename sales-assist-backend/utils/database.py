import os
from motor.motor_asyncio import AsyncIOMotorClient

# Global singletons (POC-safe)
_client: AsyncIOMotorClient | None = None
_database = None


def connect_to_mongo():
    """
    Initialize MongoDB connection.
    Called lazily on first access.
    """
    global _client, _database

    if _client is not None:
        return

    mongo_uri = os.getenv("MONGO_URI")
    db_name = os.getenv("MONGO_DB_NAME")

    if not mongo_uri or not db_name:
        raise RuntimeError("MongoDB environment variables not set")

    _client = AsyncIOMotorClient(mongo_uri)
    _database = _client[db_name]


def get_database():
    """
    Returns the MongoDB database instance.
    """
    if _database is None:
        connect_to_mongo()
    return _database


def close_mongo_connection():
    """
    Gracefully close MongoDB connection.
    """
    global _client, _database
    if _client:
        _client.close()
        _client = None
        _database = None
