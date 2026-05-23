from __future__ import annotations

from pathlib import Path
import sqlite3

import pandas as pd


class RadarStore:
    def __init__(self, database_path: Path):
        self.database_path = database_path
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.backend = "duckdb"
        try:
            import duckdb  # type: ignore

            self._duckdb = duckdb
            self._conn = duckdb.connect(str(database_path))
        except Exception:
            self.backend = "sqlite"
            sqlite_path = database_path.with_suffix(".sqlite")
            self.database_path = sqlite_path
            self._duckdb = None
            self._conn = sqlite3.connect(sqlite_path)
        self._create_schema()

    def close(self) -> None:
        self._conn.close()

    def replace_table(self, table: str, frame: pd.DataFrame) -> None:
        if self.backend == "duckdb":
            self._conn.execute(f"CREATE OR REPLACE TABLE {table} AS SELECT * FROM frame")
            return
        frame.to_sql(table, self._conn, if_exists="replace", index=False)

    def table(self, table: str) -> pd.DataFrame:
        try:
            if self.backend == "duckdb":
                return self._conn.execute(f"SELECT * FROM {table}").df()
            return pd.read_sql_query(f"SELECT * FROM {table}", self._conn)
        except Exception:
            return pd.DataFrame()

    def query(self, sql: str) -> pd.DataFrame:
        if self.backend == "duckdb":
            return self._conn.execute(sql).df()
        return pd.read_sql_query(sql, self._conn)

    def _create_schema(self) -> None:
        statements = [
            """
            CREATE TABLE IF NOT EXISTS observations (
                indicator_slug TEXT,
                observed_at TEXT,
                value DOUBLE,
                source TEXT,
                unit TEXT
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS source_status (
                source_slug TEXT,
                status TEXT,
                message TEXT,
                checked_at TEXT
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS research_mentions (
                source_slug TEXT,
                theme TEXT,
                summary TEXT,
                sentiment DOUBLE,
                published_at TEXT,
                url TEXT
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS subsector_research_profiles (
                subsector_slug TEXT,
                scope TEXT,
                current_phase_hypothesis TEXT,
                why_now TEXT,
                key_debates TEXT,
                catalysts TEXT,
                risks TEXT,
                review_status TEXT,
                updated_at TEXT
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS research_facts (
                fact_id TEXT,
                subsector_slug TEXT,
                theme TEXT,
                claim TEXT,
                source_name TEXT,
                source_url TEXT,
                source_type TEXT,
                source_quality TEXT,
                source_date TEXT,
                captured_at TEXT,
                confidence DOUBLE,
                review_status TEXT,
                evidence_scope TEXT
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS subsector_market_cycle (
                subsector_slug TEXT,
                observed_at TEXT,
                price_index DOUBLE,
                benchmark_index DOUBLE,
                relative_price_index DOUBLE,
                valuation_proxy DOUBLE,
                driver_pressure DOUBLE,
                source TEXT,
                notes TEXT
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS subsector_scores (
                slug TEXT,
                name TEXT,
                group_name TEXT,
                opportunity_score DOUBLE,
                cycle_pressure DOUBLE,
                recovery_potential DOUBLE,
                valuation_proxy DOUBLE,
                momentum DOUBLE,
                macro_tailwind DOUBLE,
                narrative_divergence DOUBLE,
                confidence DOUBLE,
                data_confidence TEXT,
                explanation TEXT,
                refreshed_at TEXT
            )
            """,
        ]
        for statement in statements:
            self._conn.execute(statement)
