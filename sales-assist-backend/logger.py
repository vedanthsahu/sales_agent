import logging
import os
import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
import sys
import traceback
import json
from logging.handlers import RotatingFileHandler


class EnhancedLogger:
    def __init__(self, name: str = "chatbot", log_dir: str = "logs"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)

        # Create logs directory if it doesn't exist
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)

        # Clear existing handlers to avoid duplicates
        if self.logger.handlers:
            self.logger.handlers.clear()

        # Setup handlers
        self._setup_handlers()

    def _setup_handlers(self):
        """Setup file and console handlers with daily rotation"""
        # Get today's date for log file naming
        today = datetime.datetime.now().strftime("%Y-%m-%d")

        # Daily log file
        daily_log_file = self.log_dir / f"chatbot_{today}.log"

        # File handler with rotation (10MB max, keep 5 backups)
        file_handler = RotatingFileHandler(
            daily_log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # Formatters
        file_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(message)s',
            datefmt='%H:%M:%S'
        )

        file_handler.setFormatter(file_formatter)
        console_handler.setFormatter(console_formatter)

        # Add handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def _sanitize_for_windows(self, text: str) -> str:
        """Sanitize text for Windows console output (cp1252 encoding)."""
        if not isinstance(text, str):
            return text
        # Replace problematic unicode characters with ASCII equivalents
        replacements = {
            '\u2011': '-',  # non-breaking hyphen
            '\u2013': '-',  # en dash
            '\u2014': '-',  # em dash
            '\u2018': "'",  # left single quote
            '\u2019': "'",  # right single quote
            '\u201c': '"',  # left double quote
            '\u201d': '"',  # right double quote
            '\u2026': '...', # ellipsis
            '\u00a0': ' ',  # non-breaking space
            '\u2022': '*',  # bullet
            '\u00b7': '*',  # middle dot
        }
        for char, replacement in replacements.items():
            text = text.replace(char, replacement)
        # Fallback: encode to ASCII, replacing unknown chars
        return text.encode('ascii', 'replace').decode('ascii')
    
    def _format_extra_data(self, extra_data: Optional[Dict[str, Any]] = None) -> str:
        """Format extra data as JSON string"""
        if not extra_data:
            return ""
        try:
            json_str = json.dumps(extra_data, default=str)
            return f" | EXTRA_DATA: {self._sanitize_for_windows(json_str)}"
        except (TypeError, ValueError):
            return f" | EXTRA_DATA: {self._sanitize_for_windows(str(extra_data))}"

    def debug(self, message: str, extra_data: Optional[Dict[str, Any]] = None):
        """Log debug message with optional extra data"""
        full_message = self._sanitize_for_windows(message) + self._format_extra_data(extra_data)
        self.logger.debug(full_message)

    def info(self, message: str, extra_data: Optional[Dict[str, Any]] = None):
        """Log info message with optional extra data"""
        full_message = self._sanitize_for_windows(message) + self._format_extra_data(extra_data)
        self.logger.info(full_message)

    def warning(self, message: str, extra_data: Optional[Dict[str, Any]] = None):
        """Log warning message with optional extra data"""
        full_message = self._sanitize_for_windows(message) + self._format_extra_data(extra_data)
        self.logger.warning(full_message)

    def error(self, message: str, extra_data: Optional[Dict[str, Any]] = None):
        """Log error message with optional extra data"""
        full_message = self._sanitize_for_windows(message) + self._format_extra_data(extra_data)
        self.logger.error(full_message)

    def custom_error(
    self,
    message: str,
    extra_data: Optional[Dict[str, Any]] = None,
    exc_info: Union[bool, BaseException, None] = None,
    extra: Optional[Dict[str, Any]] = None,
    ):
        """
        Docker-safe JSON error logger.
        Supports exc_info=True | Exception | None
        """

        log_event: Dict[str, Any] = {
            "level": "ERROR",
            "message": message,
        }

        if extra_data:
            log_event["extra_data"] = extra_data

        if extra:
            log_event.update(extra)

        # ---- FIX IS HERE ----
        if exc_info:
            if exc_info is True:
                exc_type, exc, tb = sys.exc_info()
            elif isinstance(exc_info, BaseException):
                exc_type = type(exc_info)
                exc = exc_info
                tb = exc_info.__traceback__
            else:
                exc_type = exc = tb = None

            if exc_type:
                log_event["traceback"] = "".join(
                    traceback.format_exception(exc_type, exc, tb)
                )

        self.logger.error(json.dumps(log_event))

    def critical(self, message: str, extra_data: Optional[Dict[str, Any]] = None):
        """Log critical message with optional extra data"""
        full_message = self._sanitize_for_windows(message) + self._format_extra_data(extra_data)
        self.logger.critical(full_message)

    def exception(self, message: str, exc_info: Optional[Exception] = None, extra_data: Optional[Dict[str, Any]] = None):
        """Log exception with optional extra data"""
        full_message = self._sanitize_for_windows(message) + self._format_extra_data(extra_data)
        self.logger.exception(full_message, exc_info=exc_info)

    def log_file_processing(self, filename: str, file_id: str, num_chunks: int, processing_time: float, session_id: str):
        """Log file processing details"""
        self.info(
            f"FILE_PROCESSING_COMPLETED: {filename}",
            extra_data={
                "event_type": "file_processing",
                "filename": filename,
                "file_id": file_id,
                "num_chunks": num_chunks,
                "processing_time_seconds": round(processing_time, 3),
                "session_id": session_id,
                "timestamp": datetime.datetime.utcnow().isoformat()
            }
        )

    def log_chunk_retrieval(self, question: str, retrieved_chunks: List[str], similarity_scores: List[float], session_id: str):
        """Log chunk retrieval details for RAG"""
        self.info(
            f"CHUNK_RETRIEVAL_COMPLETED",
            extra_data={
                "event_type": "chunk_retrieval",
                "question": question,
                "num_chunks_retrieved": len(retrieved_chunks),
                "similarity_scores": [round(score, 4) for score in similarity_scores],
                "chunk_previews": [chunk[:100] + "..." if len(chunk) > 100 else chunk for chunk in retrieved_chunks[:3]],
                "session_id": session_id,
                "timestamp": datetime.datetime.utcnow().isoformat()
            }
        )

    def log_llm_interaction(self, question: str, answer: str, processing_time: float, session_id: str, model_name: str = None):
        """Log LLM interaction details"""
        self.info(
            f"LLM_INTERACTION_COMPLETED",
            extra_data={
                "event_type": "llm_interaction",
                "question": question,
                "answer_length": len(answer),
                "answer_preview": answer[:200] + "..." if len(answer) > 200 else answer,
                "processing_time_seconds": round(processing_time, 3),
                "session_id": session_id,
                "model_name": model_name,
                "timestamp": datetime.datetime.utcnow().isoformat()
            }
        )

    def log_api_request(self, endpoint: str, method: str, session_id: str = None, processing_time: float = None, status_code: int = None):
        """Log API request details"""
        self.info(
            f"API_REQUEST: {method} {endpoint}",
            extra_data={
                "event_type": "api_request",
                "endpoint": endpoint,
                "method": method,
                "session_id": session_id,
                "processing_time_seconds": round(processing_time, 3) if processing_time else None,
                "status_code": status_code,
                "timestamp": datetime.datetime.utcnow().isoformat()
            }
        )

    def log_database_operation(self, operation: str, collection: str, count: int = None, processing_time: float = None):
        """Log database operation details"""
        self.debug(
            f"DATABASE_OPERATION: {operation} on {collection}",
            extra_data={
                "event_type": "database_operation",
                "operation": operation,
                "collection": collection,
                "count": count,
                "processing_time_seconds": round(processing_time, 3) if processing_time else None,
                "timestamp": datetime.datetime.utcnow().isoformat()
            }
        )

    def log_embedding_operation(self, operation: str, text_count: int, embedding_dimension: int, processing_time: float):
        """Log embedding operation details"""
        self.debug(
            f"EMBEDDING_OPERATION: {operation}",
            extra_data={
                "event_type": "embedding_operation",
                "operation": operation,
                "text_count": text_count,
                "embedding_dimension": embedding_dimension,
                "processing_time_seconds": round(processing_time, 3),
                "timestamp": datetime.datetime.utcnow().isoformat()
            }
        )

    def log_cache_operation(self, operation: str, cache_type: str, hit: bool = None, size: int = None):
        """Log cache operation details"""
        self.debug(
            f"CACHE_OPERATION: {operation} - {cache_type}",
            extra_data={
                "event_type": "cache_operation",
                "operation": operation,
                "cache_type": cache_type,
                "cache_hit": hit,
                "cache_size": size,
                "timestamp": datetime.datetime.utcnow().isoformat()
            }
        )

    # GraphRAG-specific logging functions
    def log_graph_query_classification(self, question: str, query_type: str, confidence: float = None, session_id: str = None):
        """Log graph query classification details"""
        self.info(
            f"GRAPH_QUERY_CLASSIFIED: {query_type}",
            extra_data={
                "event_type": "graph_query_classification",
                "question": question,
                "query_type": query_type,
                "confidence": confidence,
                "session_id": session_id,
                "timestamp": datetime.datetime.utcnow().isoformat()
            }
        )

    def log_graph_query_rewrite(self, original_question: str, rewritten_question: str, session_id: str = None):
        """Log graph query rewrite details"""
        self.info(
            f"GRAPH_QUERY_REWRITTEN",
            extra_data={
                "event_type": "graph_query_rewrite",
                "original_question": original_question,
                "rewritten_question": rewritten_question,
                "session_id": session_id,
                "timestamp": datetime.datetime.utcnow().isoformat()
            }
        )

    def log_graph_entity_retrieval(self, question: str, entities: List[Dict], session_id: str = None):
        """Log graph entity retrieval details"""
        entity_previews = []
        for entity in entities[:5]:  # Show first 5 entities
            preview = {
                "title": entity.get("title", "N/A"),
                "type": entity.get("type", "N/A"),
                "description": entity.get("description", "N/A")[:100] + "..." if len(entity.get("description", "")) > 100 else entity.get("description", "N/A")
            }
            entity_previews.append(preview)

        self.info(
            f"GRAPH_ENTITY_RETRIEVAL_COMPLETED: {len(entities)} entities found",
            extra_data={
                "event_type": "graph_entity_retrieval",
                "question": question,
                "num_entities": len(entities),
                "entity_previews": entity_previews,
                "session_id": session_id,
                "timestamp": datetime.datetime.utcnow().isoformat()
            }
        )

    def log_graph_relationship_retrieval(self, entities: List[str], relationships: List[Dict], session_id: str = None):
        """Log graph relationship retrieval details"""
        relationship_previews = []
        for rel in relationships[:5]:  # Show first 5 relationships
            preview = {
                "source": rel.get("source", "N/A"),
                "target": rel.get("target", "N/A"),
                "description": rel.get("description", "N/A")[:100] + "..." if len(rel.get("description", "")) > 100 else rel.get("description", "N/A")
            }
            relationship_previews.append(preview)

        self.info(
            f"GRAPH_RELATIONSHIP_RETRIEVAL_COMPLETED: {len(relationships)} relationships found",
            extra_data={
                "event_type": "graph_relationship_retrieval",
                "entities": entities,
                "num_relationships": len(relationships),
                "relationship_previews": relationship_previews,
                "session_id": session_id,
                "timestamp": datetime.datetime.utcnow().isoformat()
            }
        )

    def log_graph_chunk_retrieval(self, entities: List[str], chunks: List[str], session_id: str = None):
        """Log graph chunk retrieval details"""
        chunk_previews = [chunk[:100] + "..." if len(chunk) > 100 else chunk for chunk in chunks[:3]]

        self.info(
            f"GRAPH_CHUNK_RETRIEVAL_COMPLETED: {len(chunks)} chunks found",
            extra_data={
                "event_type": "graph_chunk_retrieval",
                "entities": entities,
                "num_chunks": len(chunks),
                "chunk_previews": chunk_previews,
                "session_id": session_id,
                "timestamp": datetime.datetime.utcnow().isoformat()
            }
        )

    def log_graph_community_retrieval(self, entities: List[str], communities: List[str], session_id: str = None):
        """Log graph community retrieval details"""
        community_previews = [community[:100] + "..." if len(community) > 100 else community for community in communities[:3]]

        self.info(
            f"GRAPH_COMMUNITY_RETRIEVAL_COMPLETED: {len(communities)} communities found",
            extra_data={
                "event_type": "graph_community_retrieval",
                "entities": entities,
                "num_communities": len(communities),
                "community_previews": community_previews,
                "session_id": session_id,
                "timestamp": datetime.datetime.utcnow().isoformat()
            }
        )

    def log_graph_answer_generation(self, question: str, context_summary: Dict[str, int], answer: str, processing_time: float, session_id: str = None):
        """Log graph answer generation details"""
        self.info(
            f"GRAPH_ANSWER_GENERATION_COMPLETED",
            extra_data={
                "event_type": "graph_answer_generation",
                "question": question,
                "context_summary": context_summary,
                "answer_length": len(answer),
                "answer_preview": answer[:200] + "..." if len(answer) > 200 else answer,
                "processing_time_seconds": round(processing_time, 3),
                "session_id": session_id,
                "timestamp": datetime.datetime.utcnow().isoformat()
            }
        )

    def log_execution_step(self, step_name: str, step_type: str, status: str, duration_ms: float, 
                          input_data: Dict[str, Any] = None, output_data: Dict[str, Any] = None,
                          llm_input: str = None, llm_output: str = None, error_message: str = None,
                          trace_id: str = None):
        """Log execution step details for GraphRAG"""
        self.info(
            f"EXECUTION_STEP: {step_name} - {status.upper()}",
            extra_data={
                "event_type": "execution_step",
                "step_name": step_name,
                "step_type": step_type,
                "status": status,
                "duration_ms": round(duration_ms, 2),
                "input_data": input_data,
                "output_data": output_data,
                "llm_input_preview": llm_input[:200] + "..." if llm_input and len(llm_input) > 200 else llm_input,
                "llm_output_preview": llm_output[:200] + "..." if llm_output and len(llm_output) > 200 else llm_output,
                "error_message": error_message,
                "trace_id": trace_id,
                "timestamp": datetime.datetime.utcnow().isoformat()
            }
        )


# Create a global logger instance
enhanced_logger = EnhancedLogger()


# Decorator for logging function execution time
def log_execution_time(logger_method: str = "debug"):
    """Decorator to log function execution time"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            import time
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                getattr(enhanced_logger, logger_method)(
                    f"Function {func.__name__} executed successfully",
                    extra_data={
                        "function_name": func.__name__,
                        "execution_time_seconds": round(execution_time, 3),
                        "timestamp": datetime.datetime.utcnow().isoformat()
                    }
                )
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                enhanced_logger.exception(
                    f"Function {func.__name__} failed",
                    exc_info=e,
                    extra_data={
                        "function_name": func.__name__,
                        "execution_time_seconds": round(execution_time, 3),
                        "error": str(e),
                        "timestamp": datetime.datetime.utcnow().isoformat()
                    }
                )
                raise
        return wrapper
    return decorator