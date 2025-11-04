import re
from typing import List

_FTS_TOKEN_RE = re.compile(r"[0-9A-Za-z_]+")


def normalise_fts_query(query: str, *, max_tokens: int = 16) -> str:
    tokens = _FTS_TOKEN_RE.findall(query.lower())
    if not tokens:
        return ""
    limited_tokens: List[str] = tokens[:max_tokens]
    return " ".join(limited_tokens)
