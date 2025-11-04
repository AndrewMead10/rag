from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass


def generate_api_key(prefix: str = "rag") -> str:
    random_part = secrets.token_urlsafe(32).replace("-", "").replace("_", "")
    return f"{prefix}_{random_part}"


def hash_api_key(key: str) -> str:
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def key_prefix(key: str, length: int = 10) -> str:
    return key[:length]


def verify_api_key(stored_hash: str, candidate: str) -> bool:
    candidate_hash = hash_api_key(candidate)
    # Use secrets.compare_digest for timing-safe comparison
    return secrets.compare_digest(stored_hash, candidate_hash)
