from __future__ import annotations

import os

import logfire

from .config import settings

_logfire_configured = False
_sqlalchemy_instrumented = False


def _should_send_to_logfire() -> str:
    """Send to LogFire only when a token is present."""
    return "if-token-present"


def setup_logfire():
    """Configure LogFire with automatic instrumentation."""
    global _logfire_configured

    if not settings.logfire_enabled or _logfire_configured:
        return

    if "LOGFIRE_IGNORE_NO_CONFIG" not in os.environ:
        os.environ["LOGFIRE_IGNORE_NO_CONFIG"] = "true" if settings.logfire_ignore_no_config else "false"

    logfire.configure(
        service_name=settings.logfire_service_name,
        service_version="1.0.0",
        environment=settings.logfire_environment,
        token=settings.logfire_token or None,
        send_to_logfire=_should_send_to_logfire(),
    )

    _logfire_configured = True

def instrument_sqlalchemy(engine):
    """Instrument SQLAlchemy engine with LogFire."""
    global _sqlalchemy_instrumented

    if not settings.logfire_enabled or _sqlalchemy_instrumented:
        return engine

    setup_logfire()
    logfire.instrument_sqlalchemy(engine=engine)
    _sqlalchemy_instrumented = True
    return engine
