"""Result storage: SQLite locally, Neon Postgres when DATABASE_URL is set."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    create_engine,
    insert,
    select,
)
from sqlalchemy.engine import Engine

from urdulens.paths import RESULTS_DIR

metadata = MetaData()

runs = Table(
    "runs",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("dataset", String(64), nullable=False),
    Column("n_samples", Integer, nullable=False),
    Column("git_sha", String(64)),
    Column("notes", Text),
)

results = Table(
    "results",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("run_id", Integer, ForeignKey("runs.id"), nullable=False, index=True),
    Column("engine", String(64), nullable=False),
    Column("engine_version", String(64)),
    Column("sample_id", String(64), nullable=False),
    Column("source", String(16), nullable=False),
    Column("content_type", String(16)),
    Column("style", String(16)),
    Column("font", String(64)),
    Column("level", String(16)),
    Column("ref", Text, nullable=False),
    Column("hyp", Text, nullable=False),
    Column("cer", Float, nullable=False),
    Column("wer", Float, nullable=False),
    Column("cer_strict", Float, nullable=False),
    Column("exact", Boolean, nullable=False),
    Column("ms", Float),
)


def database_url() -> str:
    """DATABASE_URL if set (Neon), otherwise a local SQLite file under results/."""
    url = os.environ.get("DATABASE_URL", "").strip()
    if url:
        if url.startswith("postgres://"):
            url = "postgresql://" + url[len("postgres://") :]
        return url
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{Path(RESULTS_DIR / 'urdulens.db').as_posix()}"


def get_engine(url: str | None = None) -> Engine:
    return create_engine(url or database_url(), pool_pre_ping=True, future=True)


def init_db(engine: Engine | None = None) -> Engine:
    engine = engine or get_engine()
    metadata.create_all(engine)
    return engine


def save_run(
    engine: Engine,
    dataset: str,
    rows: list[dict],
    git_sha: str | None = None,
    notes: str | None = None,
) -> int:
    """Insert one benchmark run and its per-sample rows. Returns the run id."""
    with engine.begin() as conn:
        run_id = conn.execute(
            insert(runs).values(
                created_at=datetime.now(timezone.utc),
                dataset=dataset,
                n_samples=len({r["sample_id"] for r in rows}),
                git_sha=git_sha,
                notes=notes,
            )
        ).inserted_primary_key[0]
        if rows:
            conn.execute(insert(results), [{**r, "run_id": run_id} for r in rows])
    return int(run_id)


def load_runs(engine: Engine) -> pd.DataFrame:
    with engine.connect() as conn:
        return pd.read_sql(select(runs).order_by(runs.c.id.desc()), conn)


def load_results(engine: Engine, run_id: int | None = None) -> pd.DataFrame:
    stmt = select(results)
    if run_id is not None:
        stmt = stmt.where(results.c.run_id == run_id)
    with engine.connect() as conn:
        return pd.read_sql(stmt, conn)
