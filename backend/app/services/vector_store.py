from __future__ import annotations

import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Dict
import re

from ..config import settings
from ..database import engine
from ..database.models import Project
from .vectorlab import Database, EmbeddingConfig, EmbeddingService


@dataclass(frozen=True)
class EmbeddingKey:
    provider: str
    model_repo: str
    model_file: str
    embed_dim: int


class VectorStoreRegistry:
    """Caches project-specific PostgreSQL vector stores and shared embedding services."""

    def __init__(self) -> None:
        self._dbs: Dict[int, Database] = {}
        self._embed_services: Dict[EmbeddingKey, EmbeddingService] = {}
        self._lock = threading.RLock()

    def _build_db(self, project: Project) -> Database:
        if not project.vector_store_path:
            raise ValueError("Project is missing vector store identifier")
        if not re.fullmatch(r"[a-z0-9_]+", project.vector_store_path):
            raise ValueError(f"Invalid vector store identifier: {project.vector_store_path}")
        database = Database(
            engine=engine,
            table_name=project.vector_store_path,
            project_id=project.id,
            embed_dim=project.embedding_dim,
        )
        database.connect()
        return database

    def get_database(self, project: Project) -> Database:
        with self._lock:
            db = self._dbs.get(project.id)
            if db is None:
                db = self._build_db(project)
                self._dbs[project.id] = db
            return db

    def _embedding_config(self, project: Project) -> EmbeddingConfig:
        model_repo = project.embedding_model_repo or settings.rag_model_repo
        model_file = project.embedding_model_file or settings.rag_model_filename

        return EmbeddingConfig(
            model_repo=model_repo,
            model_filename=model_file,
            model_dir=Path(settings.rag_model_dir),
            embed_dim=project.embedding_dim,
            hf_token=settings.rag_hf_token or None,
            llama_threads=settings.rag_llama_threads,
            llama_batch_size=settings.rag_llama_batch_size,
            llama_context=settings.rag_llama_context,
        )

    def get_embedder(self, project: Project) -> EmbeddingService:
        key = EmbeddingKey(
            provider=project.embedding_provider,
            model_repo=project.embedding_model_repo or settings.rag_model_repo,
            model_file=project.embedding_model_file or settings.rag_model_filename,
            embed_dim=project.embedding_dim,
        )
        with self._lock:
            embedder = self._embed_services.get(key)
            if embedder is None:
                config = self._embedding_config(project)
                embedder = EmbeddingService(config)
                self._embed_services[key] = embedder
            return embedder


vector_store_registry = VectorStoreRegistry()
