from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db_session
from ..database.models import Plan

DEFAULT_PLANS = [
    {
        "slug": "free",
        "name": "Free",
        "price_cents": 0,
        "query_qps_limit": 1,
        "ingest_qps_limit": 10,
        "project_limit": 3,
        "vector_limit": 1_000,
        "allow_topups": False,
        "polar_product_id": None,
    },
    {
        "slug": "pro",
        "name": "Pro",
        "price_cents": 1000,
        "query_qps_limit": 25,
        "ingest_qps_limit": 100,
        "project_limit": -1,
        "vector_limit": 1_000_000,
        "allow_topups": True,
        "polar_product_id": None,
    },
    {
        "slug": "scale",
        "name": "Scale",
        "price_cents": 0,
        "query_qps_limit": 250,
        "ingest_qps_limit": 1000,
        "project_limit": -1,
        "vector_limit": 10_000_000,
        "allow_topups": True,
        "polar_product_id": None,
    },
]


def seed_plans(session: Session) -> None:
    """Ensure the canonical plan definitions exist."""
    existing = {
        row.slug: row
        for row in session.execute(select(Plan)).scalars()
    }

    changed = False
    now = datetime.utcnow()

    for base_plan_data in DEFAULT_PLANS:
        plan_data = dict(base_plan_data)
        if plan_data["slug"] == "pro" and settings.polar_product_pro:
            plan_data["polar_product_id"] = settings.polar_product_pro
        plan = existing.get(plan_data["slug"])
        if plan is None:
            session.add(Plan(**plan_data, created_at=now, updated_at=now))
            changed = True
        else:
            updated = False
            for key, value in plan_data.items():
                if getattr(plan, key) != value:
                    setattr(plan, key, value)
                    updated = True
            if updated:
                plan.updated_at = now
                changed = True

    if changed:
        session.commit()
