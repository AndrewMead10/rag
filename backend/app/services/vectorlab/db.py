import hashlib
import logging
import threading
from typing import Any, List, Mapping, Optional, Sequence

from sqlalchemy import Column, DateTime, Index, Integer, MetaData, Table, Text, bindparam, func, text as sql_text
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from pgvector.sqlalchemy import Vector

logger = logging.getLogger(__name__)


def _index_name(base: str, suffix: str) -> str:
    candidate = f"{base}_{suffix}"
    if len(candidate) <= 60:
        return candidate
    digest = hashlib.sha1(candidate.encode("utf-8")).hexdigest()[:8]
    trimmed_base = base[: max(1, 50 - len(suffix))]
    return f"{trimmed_base}_{suffix}_{digest}"


class Database:
    """PostgreSQL persistence with pgvector embeddings and tsvector search."""

    def __init__(self, *, engine: Engine, table_name: str, project_id: int, embed_dim: int) -> None:
        self._engine = engine
        self._table_name = table_name
        self._project_id = project_id
        self._embed_dim = embed_dim
        self._session_factory = sessionmaker(bind=engine)
        self._lock = threading.RLock()
        self._metadata: Optional[MetaData] = None
        self._table: Optional[Table] = None
        self._is_ready = False

    def connect(self) -> None:
        if self._is_ready:
            return

        with self._lock:
            if self._is_ready:
                return

            metadata = MetaData()
            table = Table(
                self._table_name,
                metadata,
                Column("id", Integer, primary_key=True),
                Column("project_id", Integer, nullable=False, index=True),
                Column("content", Text, nullable=False),
                Column("title", Text, nullable=False),
                Column("url", Text, nullable=False),
                Column("published_at", Text, nullable=False),
                Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
                Column("embedding", Vector(self._embed_dim), nullable=False),
                Column("text_search", TSVECTOR, nullable=False),
                Column("active", Integer, nullable=False, server_default="1"),
            )

            Index(_index_name(self._table_name, "project_idx"), table.c.project_id)
            Index(
                _index_name(self._table_name, "text_idx"),
                table.c.text_search,
                postgresql_using="gin",
            )
            Index(
                _index_name(self._table_name, "embedding_idx"),
                table.c.embedding,
                postgresql_using="ivfflat",
                postgresql_ops={"embedding": "vector_cosine_ops"},
                postgresql_with={"lists": "100"},
            )

            try:
                metadata.create_all(self._engine, checkfirst=True)
            except Exception:
                logger.exception("Failed to initialise vector table %s", self._table_name)
                raise

            self._metadata = metadata
            self._table = table
            self._is_ready = True
            logger.info("pgvector table initialised for project %s (%s)", self._project_id, self._table_name)

    def close(self) -> None:
        # Engine lifecycle managed globally; nothing to dispose here.
        pass

    def is_ready(self) -> bool:
        return self._is_ready

    def insert_document(
        self,
        *,
        content: str,
        title: str,
        url: str,
        published_at: str,
        embedding: Sequence[float],
    ) -> Mapping[str, Any]:
        self._require_ready()
        if len(embedding) != self._embed_dim:
            raise ValueError(
                f"embedding dimension mismatch: expected {self._embed_dim}, got {len(embedding)}"
            )

        embedding_list: List[float] = [float(value) for value in embedding]
        stmt = (
            sql_text(
                f"""
                INSERT INTO {self._table_name} (
                    project_id,
                    content,
                    title,
                    url,
                    published_at,
                    embedding,
                    text_search
                )
                VALUES (
                    :project_id,
                    :content,
                    :title,
                    :url,
                    :published_at,
                    :embedding,
                    setweight(to_tsvector('english', coalesce(:title, '')), 'A')
                    ||
                    setweight(to_tsvector('english', coalesce(:content, '')), 'B')
                )
                RETURNING
                    id,
                    content,
                    title,
                    url,
                    published_at,
                    created_at
                """
            )
            .bindparams(bindparam("embedding", type_=Vector(self._embed_dim)))
        )

        params = {
            "project_id": self._project_id,
            "content": content,
            "title": title,
            "url": url,
            "published_at": published_at,
            "embedding": embedding_list,
        }

        with self._lock:
            session: Session = self._session_factory()
            try:
                result = session.execute(stmt, params)
                row = result.mappings().first()
                session.commit()
            except Exception:
                session.rollback()
                logger.exception("Failed to insert document for project %s", self._project_id)
                raise
            finally:
                session.close()

        if row is None:
            raise RuntimeError("Failed to retrieve inserted document row")
        return dict(row)

    def fetch_document(self, doc_id: int) -> Optional[Mapping[str, Any]]:
        self._require_ready()
        stmt = sql_text(
            f"""
            SELECT
                id,
                content,
                title,
                url,
                published_at,
                created_at
            FROM {self._table_name}
            WHERE id = :doc_id AND active = 1
            LIMIT 1
            """
        )

        with self._lock:
            session: Session = self._session_factory()
            try:
                result = session.execute(stmt, {"doc_id": doc_id})
                row = result.mappings().first()
                session.commit()
            except Exception:
                session.rollback()
                logger.exception("Failed to fetch document %s for project %s", doc_id, self._project_id)
                raise
            finally:
                session.close()

        return dict(row) if row else None

    def delete_document(self, doc_id: int) -> bool:
        self._require_ready()
        stmt = sql_text(
            f"""
            DELETE FROM {self._table_name}
            WHERE id = :doc_id
            RETURNING 1
            """
        )

        with self._lock:
            session: Session = self._session_factory()
            try:
                result = session.execute(stmt, {"doc_id": doc_id})
                deleted = result.scalar() is not None
                session.commit()
            except Exception:
                session.rollback()
                logger.exception("Failed to delete document %s for project %s", doc_id, self._project_id)
                raise
            finally:
                session.close()

        return deleted

    def hybrid_search(
        self,
        *,
        embedding: Sequence[float],
        fts_query: Optional[str],
        top_k: int,
        vector_k: int,
        weight_vector: float,
        weight_text: float,
    ) -> List[Mapping[str, Any]]:
        self._require_ready()
        if len(embedding) != self._embed_dim:
            raise ValueError(
                f"embedding dimension mismatch: expected {self._embed_dim}, got {len(embedding)}"
            )

        embedding_list: List[float] = [float(value) for value in embedding]
        params: dict[str, Any] = {
            "embedding": embedding_list,
            "top_k": top_k,
            "vector_k": vector_k,
            "weight_vector": weight_vector,
            "weight_text": weight_text,
        }

        text_clause = ""
        if fts_query:
            params["fts_query"] = fts_query
            params["text_k"] = max(vector_k, top_k)
            text_clause = f"""
            text_matches AS (
                SELECT
                    id AS doc_id,
                    ts_rank(
                        text_search,
                        websearch_to_tsquery('english', :fts_query)
                    ) AS text_score
                FROM {self._table_name}
                WHERE websearch_to_tsquery('english', :fts_query) @@ text_search AND active = 1
                ORDER BY text_score DESC
                LIMIT :text_k
            ),
            """
        else:
            text_clause = """
            text_matches AS (
                SELECT NULL::integer AS doc_id, NULL::real AS text_score
                WHERE FALSE
            ),
            """

        query = (
            sql_text(
                f"""
                WITH
                vector_matches AS (
                    SELECT
                        id AS doc_id,
                        (1 - (embedding <=> :embedding)) AS vector_score,
                        (embedding <=> :embedding) AS vector_distance
                    FROM {self._table_name}
                    WHERE active = 1
                    ORDER BY embedding <=> :embedding
                    LIMIT :vector_k
                ),
                {text_clause}
                combined AS (
                    SELECT
                        doc_id,
                        MAX(vector_score) AS vector_score,
                        MAX(text_score) AS text_score,
                        MIN(vector_distance) AS vector_distance
                    FROM (
                        SELECT doc_id, vector_score, NULL::real AS text_score, vector_distance
                        FROM vector_matches
                        UNION ALL
                        SELECT doc_id, NULL::real AS vector_score, text_score, NULL::real AS vector_distance
                        FROM text_matches
                    ) AS unioned
                    WHERE doc_id IS NOT NULL
                    GROUP BY doc_id
                )
                SELECT
                    d.id,
                    d.content,
                    d.title,
                    d.url,
                    d.published_at,
                    d.created_at,
                    COALESCE(c.vector_distance, 1.0) AS vector_distance,
                    COALESCE(c.text_score, 0.0) AS text_score,
                    (
                        COALESCE(c.vector_score, 0.0) * :weight_vector
                        +
                        COALESCE(c.text_score, 0.0) * :weight_text
                    ) AS hybrid_score
                FROM combined c
                JOIN {self._table_name} d ON d.id = c.doc_id
                ORDER BY hybrid_score DESC
                LIMIT :top_k
                """
            )
            .bindparams(bindparam("embedding", type_=Vector(self._embed_dim)))
        )

        with self._lock:
            session: Session = self._session_factory()
            try:
                probes = max(1, min(64, vector_k))
                session.execute(sql_text("SET LOCAL ivfflat.probes = :probes"), {"probes": probes})
                result = session.execute(query, params)
                rows = result.mappings().all()
                session.commit()
            except Exception:
                session.rollback()
                logger.exception("Hybrid search failed for project %s", self._project_id)
                raise
            finally:
                session.close()

        return [dict(row) for row in rows]

    def debug_vector_matches(
        self,
        *,
        embedding: Sequence[float],
        k: int,
    ) -> List[Mapping[str, Any]]:
        self._require_ready()
        embedding_list: List[float] = [float(value) for value in embedding]
        stmt = (
            sql_text(
                f"""
                SELECT
                    id,
                    title,
                    embedding <=> :embedding AS vector_distance
                FROM {self._table_name}
                WHERE active = 1
                ORDER BY embedding <=> :embedding
                LIMIT :k
                """
            )
            .bindparams(bindparam("embedding", type_=Vector(self._embed_dim)))
        )
        params = {"embedding": embedding_list, "k": k}

        with self._lock:
            session: Session = self._session_factory()
            try:
                session.execute(sql_text("SET LOCAL ivfflat.probes = :probes"), {"probes": max(1, min(64, k))})
                result = session.execute(stmt, params)
                rows = result.mappings().all()
                session.commit()
            except Exception:
                session.rollback()
                logger.exception("Vector debug query failed for project %s", self._project_id)
                raise
            finally:
                session.close()

        return [dict(row) for row in rows]

    def debug_text_matches(self, *, fts_query: str, limit: int) -> List[Mapping[str, Any]]:
        self._require_ready()
        if not fts_query:
            return []

        stmt = sql_text(
            f"""
            SELECT
                id,
                title,
                ts_rank(
                    text_search,
                    websearch_to_tsquery('english', :fts_query)
                ) AS text_score
            FROM {self._table_name}
            WHERE websearch_to_tsquery('english', :fts_query) @@ text_search AND active = 1
            ORDER BY text_score DESC
            LIMIT :limit
            """
        )
        params = {"fts_query": fts_query, "limit": limit}

        with self._lock:
            session: Session = self._session_factory()
            try:
                result = session.execute(stmt, params)
                rows = result.mappings().all()
                session.commit()
            except Exception:
                session.rollback()
                logger.exception("Text debug query failed for project %s", self._project_id)
                raise
            finally:
                session.close()

        return [dict(row) for row in rows]

    def count_documents(self) -> int:
        self._require_ready()
        with self._lock:
            session: Session = self._session_factory()
            try:
                result = session.execute(sql_text(f"SELECT COUNT(*) FROM {self._table_name} WHERE active = 1"))
                count = int(result.scalar() or 0)
                session.commit()
            except Exception:
                session.rollback()
                logger.exception("Failed to count documents for project %s", self._project_id)
                raise
            finally:
                session.close()

        return count

    def _require_ready(self) -> None:
        if not self._is_ready:
            raise RuntimeError("database connection has not been initialised")
