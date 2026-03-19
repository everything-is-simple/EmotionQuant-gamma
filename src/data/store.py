from __future__ import annotations

"""DuckDB 存储网关。

这里守住的是系统的数据合同：schema 版本、DDL、迁移、bulk upsert 和
fetch progress 都从这里统一出入口。
"""

import json
import os
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

import duckdb
import pandas as pd

CURRENT_SCHEMA_VERSION = 20


@dataclass(frozen=True)
class SchemaVersion:
    schema_version: int
    updated_at: datetime | None


class Store:
    """DuckDB 统一存储网关。"""

    def __init__(self, db_path: str | Path):
        path = Path(db_path).expanduser().resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        self.db_path = path
        self.conn = duckdb.connect(str(path))
        memory_limit = os.getenv("DUCKDB_MEMORY_LIMIT", "").strip()
        if memory_limit:
            # 长窗口证据重跑允许通过环境变量放宽 DuckDB 会话内存，不改变默认仓库口径。
            self.conn.execute(f"SET memory_limit='{memory_limit}'")
        try:
            self.conn.execute("PRAGMA enable_wal")
        except duckdb.Error:
            # Some DuckDB versions may not expose this PRAGMA.
            pass
        self._init_tables()
        self._ensure_schema_version(CURRENT_SCHEMA_VERSION)

    def _init_tables(self) -> None:
        for ddl in self._all_ddls():
            self.conn.execute(ddl)
        self._ensure_optional_columns()

    def _apply_schema_migrations(self, db_version: int, current_version: int) -> None:
        version = int(db_version)
        while version < current_version:
            next_version = version + 1
            migrate = getattr(self, f"_migrate_schema_v{version}_to_v{next_version}", None)
            if migrate is None:
                raise RuntimeError(
                    "Schema migration required. Rebuild DB or provide migration script "
                    f"(db={db_version}, code={current_version})."
                )
            migrate()
            self.conn.execute(
                """
                UPDATE _meta_schema_version
                SET schema_version = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = 1
                """,
                [next_version],
            )
            version = next_version

    def _migrate_schema_v1_to_v2(self) -> None:
        statements = [
            "ALTER TABLE l4_orders ADD COLUMN IF NOT EXISTS position_id VARCHAR",
            "ALTER TABLE l4_orders ADD COLUMN IF NOT EXISTS exit_plan_id VARCHAR",
            "ALTER TABLE l4_orders ADD COLUMN IF NOT EXISTS exit_leg_seq INTEGER",
            "ALTER TABLE l4_orders ADD COLUMN IF NOT EXISTS exit_leg_count INTEGER",
            "ALTER TABLE l4_orders ADD COLUMN IF NOT EXISTS exit_reason_code VARCHAR",
            "ALTER TABLE l4_orders ADD COLUMN IF NOT EXISTS is_partial_exit BOOLEAN DEFAULT FALSE",
            "ALTER TABLE l4_orders ADD COLUMN IF NOT EXISTS remaining_qty_before INTEGER",
            "ALTER TABLE l4_orders ADD COLUMN IF NOT EXISTS target_qty_after INTEGER",
            "ALTER TABLE l4_trades ADD COLUMN IF NOT EXISTS position_id VARCHAR",
            "ALTER TABLE l4_trades ADD COLUMN IF NOT EXISTS exit_plan_id VARCHAR",
            "ALTER TABLE l4_trades ADD COLUMN IF NOT EXISTS exit_leg_seq INTEGER",
            "ALTER TABLE l4_trades ADD COLUMN IF NOT EXISTS exit_reason_code VARCHAR",
            "ALTER TABLE l4_trades ADD COLUMN IF NOT EXISTS is_partial_exit BOOLEAN DEFAULT FALSE",
            "ALTER TABLE l4_trades ADD COLUMN IF NOT EXISTS remaining_qty_after INTEGER",
            "ALTER TABLE broker_order_lifecycle_trace_exp ADD COLUMN IF NOT EXISTS position_id VARCHAR",
            "ALTER TABLE broker_order_lifecycle_trace_exp ADD COLUMN IF NOT EXISTS exit_plan_id VARCHAR",
            "ALTER TABLE broker_order_lifecycle_trace_exp ADD COLUMN IF NOT EXISTS exit_leg_seq INTEGER",
            "ALTER TABLE broker_order_lifecycle_trace_exp ADD COLUMN IF NOT EXISTS exit_leg_count INTEGER",
            "ALTER TABLE broker_order_lifecycle_trace_exp ADD COLUMN IF NOT EXISTS exit_reason_code VARCHAR",
            "ALTER TABLE broker_order_lifecycle_trace_exp ADD COLUMN IF NOT EXISTS is_partial_exit BOOLEAN DEFAULT FALSE",
            "ALTER TABLE broker_order_lifecycle_trace_exp ADD COLUMN IF NOT EXISTS remaining_qty_before INTEGER",
            "ALTER TABLE broker_order_lifecycle_trace_exp ADD COLUMN IF NOT EXISTS remaining_qty_after INTEGER",
        ]
        for sql in statements:
            self.conn.execute(sql)

    def _migrate_schema_v2_to_v3(self) -> None:
        statements = [
            "ALTER TABLE l4_orders ADD COLUMN IF NOT EXISTS exit_leg_id VARCHAR",
            "ALTER TABLE l4_trades ADD COLUMN IF NOT EXISTS exit_leg_id VARCHAR",
            "ALTER TABLE broker_order_lifecycle_trace_exp ADD COLUMN IF NOT EXISTS exit_leg_id VARCHAR",
        ]
        for sql in statements:
            self.conn.execute(sql)

    def _migrate_schema_v3_to_v4(self) -> None:
        statements = [
            """
            CREATE TABLE IF NOT EXISTS l3_gene_wave (
                code                        VARCHAR NOT NULL,
                wave_id                     VARCHAR NOT NULL,
                direction                   VARCHAR,
                start_date                  DATE,
                end_date                    DATE,
                start_price                 DOUBLE,
                end_price                   DOUBLE,
                signed_return_pct           DOUBLE,
                magnitude_pct               DOUBLE,
                duration_trade_days         INTEGER,
                extreme_count               INTEGER,
                extreme_density             DOUBLE,
                last_extreme_date           DATE,
                last_extreme_price          DOUBLE,
                two_b_failure_count         INTEGER,
                end_confirm_index           INTEGER,
                trend_level                 VARCHAR,
                trend_direction_before      VARCHAR,
                trend_direction_after       VARCHAR,
                context_trend_level         VARCHAR,
                context_trend_direction_before VARCHAR,
                context_trend_direction_after VARCHAR,
                wave_role                   VARCHAR,
                wave_role_basis             VARCHAR,
                reversal_tag                VARCHAR,
                history_sample_size         INTEGER,
                magnitude_rank              INTEGER,
                duration_rank               INTEGER,
                extreme_density_rank        INTEGER,
                magnitude_percentile        DOUBLE,
                duration_percentile         DOUBLE,
                extreme_density_percentile  DOUBLE,
                magnitude_zscore            DOUBLE,
                duration_zscore             DOUBLE,
                extreme_density_zscore      DOUBLE,
                created_at                  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (code, wave_id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS l3_gene_event (
                code                    VARCHAR NOT NULL,
                wave_id                 VARCHAR NOT NULL,
                event_date              DATE    NOT NULL,
                event_seq               INTEGER NOT NULL,
                direction               VARCHAR,
                event_type              VARCHAR,
                event_price             DOUBLE,
                previous_extreme_price  DOUBLE,
                spacing_trade_days      INTEGER,
                density_after_event     DOUBLE,
                is_two_b_failure        BOOLEAN,
                failure_date            DATE,
                created_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (code, wave_id, event_seq)
            )
            """,
        ]
        gene_snapshot_columns = [
            ("trend_direction", "VARCHAR"),
            ("current_wave_id", "VARCHAR"),
            ("current_wave_direction", "VARCHAR"),
            ("current_wave_role", "VARCHAR"),
            ("reversal_state", "VARCHAR"),
            ("latest_completed_reversal_tag", "VARCHAR"),
            ("current_wave_start_date", "DATE"),
            ("current_wave_reference_price", "DOUBLE"),
            ("current_wave_terminal_price", "DOUBLE"),
            ("current_wave_age_trade_days", "INTEGER"),
            ("current_wave_signed_return_pct", "DOUBLE"),
            ("current_wave_magnitude_pct", "DOUBLE"),
            ("current_wave_extreme_count", "INTEGER"),
            ("current_wave_extreme_density", "DOUBLE"),
            ("current_wave_last_extreme_seq", "INTEGER"),
            ("current_wave_last_extreme_date", "DATE"),
            ("current_wave_last_extreme_price", "DOUBLE"),
            ("current_wave_two_b_failure_count", "INTEGER"),
            ("current_wave_history_sample_size", "INTEGER"),
            ("current_wave_magnitude_rank", "INTEGER"),
            ("current_wave_duration_rank", "INTEGER"),
            ("current_wave_extreme_density_rank", "INTEGER"),
            ("current_wave_magnitude_percentile", "DOUBLE"),
            ("current_wave_duration_percentile", "DOUBLE"),
            ("current_wave_extreme_density_percentile", "DOUBLE"),
            ("current_wave_magnitude_zscore", "DOUBLE"),
            ("current_wave_duration_zscore", "DOUBLE"),
            ("current_wave_extreme_density_zscore", "DOUBLE"),
            ("cross_section_magnitude_rank", "INTEGER"),
            ("cross_section_magnitude_percentile", "DOUBLE"),
            ("cross_section_duration_rank", "INTEGER"),
            ("cross_section_duration_percentile", "DOUBLE"),
            ("cross_section_extreme_density_rank", "INTEGER"),
            ("cross_section_extreme_density_percentile", "DOUBLE"),
        ]
        for column, definition in gene_snapshot_columns:
            statements.append(f"ALTER TABLE l3_stock_gene ADD COLUMN IF NOT EXISTS {column} {definition}")
        for sql in statements:
            self.conn.execute(sql)

    def _migrate_schema_v4_to_v5(self) -> None:
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS l3_gene_factor_eval (
                calc_date                   DATE    NOT NULL,
                factor_name                 VARCHAR NOT NULL,
                sample_scope                VARCHAR NOT NULL,
                direction_scope             VARCHAR NOT NULL,
                forward_horizon_trade_days  INTEGER NOT NULL,
                bin_method                  VARCHAR NOT NULL,
                bin_label                   VARCHAR NOT NULL,
                sample_size                 INTEGER,
                continuation_rate           DOUBLE,
                reversal_rate               DOUBLE,
                median_forward_return       DOUBLE,
                median_forward_drawdown     DOUBLE,
                monotonicity_score          DOUBLE,
                created_at                  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (
                    calc_date,
                    factor_name,
                    sample_scope,
                    direction_scope,
                    forward_horizon_trade_days,
                    bin_label
                )
            )
            """
        )

    def _migrate_schema_v5_to_v6(self) -> None:
        statements = [
            """
            CREATE TABLE IF NOT EXISTS l3_gene_distribution_eval (
                code                       VARCHAR NOT NULL,
                calc_date                  DATE    NOT NULL,
                current_wave_id            VARCHAR NOT NULL,
                direction                  VARCHAR NOT NULL,
                metric_name                VARCHAR NOT NULL,
                sample_scope               VARCHAR NOT NULL,
                band_method                VARCHAR NOT NULL,
                history_sample_size        INTEGER,
                band_sample_size           INTEGER,
                current_value              DOUBLE,
                current_percentile         DOUBLE,
                threshold_p65              DOUBLE,
                threshold_p95              DOUBLE,
                band_label                 VARCHAR,
                continuation_base_rate     DOUBLE,
                reversal_base_rate         DOUBLE,
                median_forward_return      DOUBLE,
                median_forward_drawdown    DOUBLE,
                created_at                 TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (code, calc_date, metric_name)
            )
            """,
            "ALTER TABLE l3_gene_wave ADD COLUMN IF NOT EXISTS magnitude_q25 DOUBLE",
            "ALTER TABLE l3_gene_wave ADD COLUMN IF NOT EXISTS magnitude_q50 DOUBLE",
            "ALTER TABLE l3_gene_wave ADD COLUMN IF NOT EXISTS magnitude_q75 DOUBLE",
            "ALTER TABLE l3_gene_wave ADD COLUMN IF NOT EXISTS magnitude_p65 DOUBLE",
            "ALTER TABLE l3_gene_wave ADD COLUMN IF NOT EXISTS magnitude_p95 DOUBLE",
            "ALTER TABLE l3_gene_wave ADD COLUMN IF NOT EXISTS magnitude_band VARCHAR",
            "ALTER TABLE l3_gene_wave ADD COLUMN IF NOT EXISTS duration_q25 DOUBLE",
            "ALTER TABLE l3_gene_wave ADD COLUMN IF NOT EXISTS duration_q50 DOUBLE",
            "ALTER TABLE l3_gene_wave ADD COLUMN IF NOT EXISTS duration_q75 DOUBLE",
            "ALTER TABLE l3_gene_wave ADD COLUMN IF NOT EXISTS duration_p65 DOUBLE",
            "ALTER TABLE l3_gene_wave ADD COLUMN IF NOT EXISTS duration_p95 DOUBLE",
            "ALTER TABLE l3_gene_wave ADD COLUMN IF NOT EXISTS duration_band VARCHAR",
            "ALTER TABLE l3_gene_wave ADD COLUMN IF NOT EXISTS wave_age_band VARCHAR",
            "ALTER TABLE l3_stock_gene ADD COLUMN IF NOT EXISTS current_wave_magnitude_q25 DOUBLE",
            "ALTER TABLE l3_stock_gene ADD COLUMN IF NOT EXISTS current_wave_magnitude_q50 DOUBLE",
            "ALTER TABLE l3_stock_gene ADD COLUMN IF NOT EXISTS current_wave_magnitude_q75 DOUBLE",
            "ALTER TABLE l3_stock_gene ADD COLUMN IF NOT EXISTS current_wave_magnitude_p65 DOUBLE",
            "ALTER TABLE l3_stock_gene ADD COLUMN IF NOT EXISTS current_wave_magnitude_p95 DOUBLE",
            "ALTER TABLE l3_stock_gene ADD COLUMN IF NOT EXISTS current_wave_magnitude_band VARCHAR",
            "ALTER TABLE l3_stock_gene ADD COLUMN IF NOT EXISTS current_wave_duration_q25 DOUBLE",
            "ALTER TABLE l3_stock_gene ADD COLUMN IF NOT EXISTS current_wave_duration_q50 DOUBLE",
            "ALTER TABLE l3_stock_gene ADD COLUMN IF NOT EXISTS current_wave_duration_q75 DOUBLE",
            "ALTER TABLE l3_stock_gene ADD COLUMN IF NOT EXISTS current_wave_duration_p65 DOUBLE",
            "ALTER TABLE l3_stock_gene ADD COLUMN IF NOT EXISTS current_wave_duration_p95 DOUBLE",
            "ALTER TABLE l3_stock_gene ADD COLUMN IF NOT EXISTS current_wave_duration_band VARCHAR",
            "ALTER TABLE l3_stock_gene ADD COLUMN IF NOT EXISTS current_wave_age_band VARCHAR",
        ]
        for sql in statements:
            self.conn.execute(sql)

    def _migrate_schema_v11_to_v12(self) -> None:
        # Phase 7B：活跃行业成员合同从 `l1_sw_industry_member`
        # 收口到 `l1_industry_member`。迁移时保留旧表，
        # 只复制数据和 fetch progress，保证旧库平滑升级。
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS l1_industry_member (
                industry_code     VARCHAR NOT NULL,
                industry_name     VARCHAR NOT NULL,
                ts_code           VARCHAR NOT NULL,
                in_date           DATE    NOT NULL,
                out_date          DATE,
                is_new            VARCHAR,
                source_trade_date DATE,
                PRIMARY KEY (industry_code, ts_code, in_date)
            )
            """
        )
        old_exists = self.read_scalar(
            """
            SELECT COUNT(*)
            FROM information_schema.tables
            WHERE table_name = 'l1_sw_industry_member'
            """
        )
        if old_exists:
            self.conn.execute(
                """
                INSERT OR REPLACE INTO l1_industry_member(
                    industry_code,
                    industry_name,
                    ts_code,
                    in_date,
                    out_date,
                    is_new,
                    source_trade_date
                )
                SELECT
                    industry_code,
                    industry_name,
                    ts_code,
                    in_date,
                    out_date,
                    is_new,
                    source_trade_date
                FROM l1_sw_industry_member
                """
            )
        self.conn.execute(
            """
            INSERT OR REPLACE INTO _meta_fetch_progress(data_type, last_success, last_attempt, status, error_msg)
            SELECT
                'industry_member' AS data_type,
                last_success,
                last_attempt,
                status,
                error_msg
            FROM _meta_fetch_progress
            WHERE data_type = 'sw_industry_member'
            """
        )

    def _migrate_schema_v12_to_v13(self) -> None:
        statements = [
            "ALTER TABLE l3_gene_event ADD COLUMN IF NOT EXISTS confirmation_window_bars INTEGER",
            "ALTER TABLE l3_gene_event ADD COLUMN IF NOT EXISTS confirmation_window_basis VARCHAR",
            "ALTER TABLE l3_gene_wave ADD COLUMN IF NOT EXISTS two_b_window_bars INTEGER",
            "ALTER TABLE l3_gene_wave ADD COLUMN IF NOT EXISTS two_b_window_basis VARCHAR",
            "ALTER TABLE l3_stock_gene ADD COLUMN IF NOT EXISTS current_two_b_window_bars INTEGER",
            "ALTER TABLE l3_stock_gene ADD COLUMN IF NOT EXISTS current_two_b_window_basis VARCHAR",
        ]
        for sql in statements:
            self.conn.execute(sql)

    def _migrate_schema_v13_to_v14(self) -> None:
        statements = [
            "ALTER TABLE l3_gene_event ADD COLUMN IF NOT EXISTS structure_condition VARCHAR",
            "ALTER TABLE l3_gene_wave ADD COLUMN IF NOT EXISTS turn_step1_condition VARCHAR",
            "ALTER TABLE l3_gene_wave ADD COLUMN IF NOT EXISTS turn_step2_condition VARCHAR",
            "ALTER TABLE l3_gene_wave ADD COLUMN IF NOT EXISTS turn_step3_condition VARCHAR",
        ]
        for sql in statements:
            self.conn.execute(sql)

    def _migrate_schema_v14_to_v15(self) -> None:
        statements = []
        level_prefixes = ["short", "intermediate", "long"]
        for prefix in level_prefixes:
            statements.extend(
                [
                    f"ALTER TABLE l3_stock_gene ADD COLUMN IF NOT EXISTS current_{prefix}_trend_level VARCHAR",
                    f"ALTER TABLE l3_stock_gene ADD COLUMN IF NOT EXISTS current_{prefix}_wave_id VARCHAR",
                    f"ALTER TABLE l3_stock_gene ADD COLUMN IF NOT EXISTS current_{prefix}_wave_direction VARCHAR",
                    f"ALTER TABLE l3_stock_gene ADD COLUMN IF NOT EXISTS current_{prefix}_context_trend_level VARCHAR",
                    f"ALTER TABLE l3_stock_gene ADD COLUMN IF NOT EXISTS current_{prefix}_context_trend_direction VARCHAR",
                    f"ALTER TABLE l3_stock_gene ADD COLUMN IF NOT EXISTS current_{prefix}_wave_role VARCHAR",
                    f"ALTER TABLE l3_stock_gene ADD COLUMN IF NOT EXISTS current_{prefix}_wave_role_basis VARCHAR",
                    f"ALTER TABLE l3_stock_gene ADD COLUMN IF NOT EXISTS current_{prefix}_two_b_window_bars INTEGER",
                    f"ALTER TABLE l3_stock_gene ADD COLUMN IF NOT EXISTS current_{prefix}_two_b_window_basis VARCHAR",
                    f"ALTER TABLE l3_stock_gene ADD COLUMN IF NOT EXISTS current_{prefix}_wave_start_date DATE",
                    f"ALTER TABLE l3_stock_gene ADD COLUMN IF NOT EXISTS current_{prefix}_wave_age_trade_days INTEGER",
                ]
            )
        for sql in statements:
            self.conn.execute(sql)

    def _migrate_schema_v15_to_v16(self) -> None:
        statements = [
            "ALTER TABLE l3_stock_gene ADD COLUMN IF NOT EXISTS current_wave_history_reference_trade_days INTEGER",
            "ALTER TABLE l3_stock_gene ADD COLUMN IF NOT EXISTS current_wave_history_span_trade_days INTEGER",
            "ALTER TABLE l3_stock_gene ADD COLUMN IF NOT EXISTS current_wave_lifespan_joint_percentile DOUBLE",
            "ALTER TABLE l3_stock_gene ADD COLUMN IF NOT EXISTS current_wave_lifespan_joint_band VARCHAR",
            "ALTER TABLE l3_stock_gene ADD COLUMN IF NOT EXISTS current_wave_prior_mainstream_wave_id VARCHAR",
            "ALTER TABLE l3_stock_gene ADD COLUMN IF NOT EXISTS current_wave_prior_mainstream_magnitude_pct DOUBLE",
            "ALTER TABLE l3_stock_gene ADD COLUMN IF NOT EXISTS current_wave_retracement_vs_prior_mainstream_pct DOUBLE",
            "ALTER TABLE l3_gene_wave ADD COLUMN IF NOT EXISTS history_reference_trade_days INTEGER",
            "ALTER TABLE l3_gene_wave ADD COLUMN IF NOT EXISTS history_span_trade_days INTEGER",
            "ALTER TABLE l3_gene_wave ADD COLUMN IF NOT EXISTS lifespan_joint_percentile DOUBLE",
            "ALTER TABLE l3_gene_wave ADD COLUMN IF NOT EXISTS lifespan_joint_band VARCHAR",
            "ALTER TABLE l3_gene_wave ADD COLUMN IF NOT EXISTS prior_mainstream_wave_id VARCHAR",
            "ALTER TABLE l3_gene_wave ADD COLUMN IF NOT EXISTS prior_mainstream_magnitude_pct DOUBLE",
            "ALTER TABLE l3_gene_wave ADD COLUMN IF NOT EXISTS retracement_vs_prior_mainstream_pct DOUBLE",
        ]
        for sql in statements:
            self.conn.execute(sql)

    def _migrate_schema_v16_to_v17(self) -> None:
        statements = [
            "ALTER TABLE l3_stock_gene ADD COLUMN IF NOT EXISTS current_context_view_scope VARCHAR",
            "ALTER TABLE l3_stock_gene ADD COLUMN IF NOT EXISTS current_context_view_level VARCHAR",
            "ALTER TABLE l3_stock_gene ADD COLUMN IF NOT EXISTS current_context_parent_trend_level VARCHAR",
            "ALTER TABLE l3_stock_gene ADD COLUMN IF NOT EXISTS current_context_parent_trend_direction VARCHAR",
            "ALTER TABLE l3_stock_gene ADD COLUMN IF NOT EXISTS reversal_state_family VARCHAR",
            "ALTER TABLE l3_stock_gene ADD COLUMN IF NOT EXISTS reversal_state_is_confirmed_turn BOOLEAN",
            "ALTER TABLE l3_stock_gene ADD COLUMN IF NOT EXISTS reversal_state_is_two_b_watch BOOLEAN",
            "ALTER TABLE l3_stock_gene ADD COLUMN IF NOT EXISTS reversal_state_is_countertrend_watch BOOLEAN",
            "ALTER TABLE l3_stock_gene ADD COLUMN IF NOT EXISTS current_wave_age_band_basis VARCHAR",
            "ALTER TABLE l3_gene_wave ADD COLUMN IF NOT EXISTS wave_age_band_basis VARCHAR",
        ]
        for sql in statements:
            self.conn.execute(sql)

    def _migrate_schema_v17_to_v18(self) -> None:
        statements = [
            "ALTER TABLE l3_stock_gene ADD COLUMN IF NOT EXISTS current_wave_magnitude_q25 DOUBLE",
            "ALTER TABLE l3_stock_gene ADD COLUMN IF NOT EXISTS current_wave_magnitude_q50 DOUBLE",
            "ALTER TABLE l3_stock_gene ADD COLUMN IF NOT EXISTS current_wave_magnitude_q75 DOUBLE",
            "ALTER TABLE l3_stock_gene ADD COLUMN IF NOT EXISTS current_wave_duration_q25 DOUBLE",
            "ALTER TABLE l3_stock_gene ADD COLUMN IF NOT EXISTS current_wave_duration_q50 DOUBLE",
            "ALTER TABLE l3_stock_gene ADD COLUMN IF NOT EXISTS current_wave_duration_q75 DOUBLE",
            "ALTER TABLE l3_gene_wave ADD COLUMN IF NOT EXISTS magnitude_q25 DOUBLE",
            "ALTER TABLE l3_gene_wave ADD COLUMN IF NOT EXISTS magnitude_q50 DOUBLE",
            "ALTER TABLE l3_gene_wave ADD COLUMN IF NOT EXISTS magnitude_q75 DOUBLE",
            "ALTER TABLE l3_gene_wave ADD COLUMN IF NOT EXISTS duration_q25 DOUBLE",
            "ALTER TABLE l3_gene_wave ADD COLUMN IF NOT EXISTS duration_q50 DOUBLE",
            "ALTER TABLE l3_gene_wave ADD COLUMN IF NOT EXISTS duration_q75 DOUBLE",
            "ALTER TABLE l3_gene_distribution_eval ADD COLUMN IF NOT EXISTS threshold_q25 DOUBLE",
            "ALTER TABLE l3_gene_distribution_eval ADD COLUMN IF NOT EXISTS threshold_q50 DOUBLE",
            "ALTER TABLE l3_gene_distribution_eval ADD COLUMN IF NOT EXISTS threshold_q75 DOUBLE",
        ]
        for sql in statements:
            self.conn.execute(sql)

    def _migrate_schema_v18_to_v19(self) -> None:
        statements = [
            "ALTER TABLE l3_stock_gene ADD COLUMN IF NOT EXISTS current_wave_magnitude_remaining_prob DOUBLE",
            "ALTER TABLE l3_stock_gene ADD COLUMN IF NOT EXISTS current_wave_duration_remaining_prob DOUBLE",
            "ALTER TABLE l3_stock_gene ADD COLUMN IF NOT EXISTS current_wave_lifespan_average_remaining_prob DOUBLE",
            "ALTER TABLE l3_stock_gene ADD COLUMN IF NOT EXISTS current_wave_lifespan_average_aged_prob DOUBLE",
            "ALTER TABLE l3_stock_gene ADD COLUMN IF NOT EXISTS current_wave_lifespan_remaining_vs_aged_odds DOUBLE",
            "ALTER TABLE l3_stock_gene ADD COLUMN IF NOT EXISTS current_wave_lifespan_aged_vs_remaining_odds DOUBLE",
            "ALTER TABLE l3_gene_wave ADD COLUMN IF NOT EXISTS magnitude_remaining_prob DOUBLE",
            "ALTER TABLE l3_gene_wave ADD COLUMN IF NOT EXISTS duration_remaining_prob DOUBLE",
            "ALTER TABLE l3_gene_wave ADD COLUMN IF NOT EXISTS lifespan_average_remaining_prob DOUBLE",
            "ALTER TABLE l3_gene_wave ADD COLUMN IF NOT EXISTS lifespan_average_aged_prob DOUBLE",
            "ALTER TABLE l3_gene_wave ADD COLUMN IF NOT EXISTS lifespan_remaining_vs_aged_odds DOUBLE",
            "ALTER TABLE l3_gene_wave ADD COLUMN IF NOT EXISTS lifespan_aged_vs_remaining_odds DOUBLE",
            "ALTER TABLE l3_gene_distribution_eval ADD COLUMN IF NOT EXISTS current_metric_remaining_prob DOUBLE",
            "ALTER TABLE l3_gene_distribution_eval ADD COLUMN IF NOT EXISTS current_metric_aged_prob DOUBLE",
            "ALTER TABLE l3_gene_distribution_eval ADD COLUMN IF NOT EXISTS current_average_remaining_prob DOUBLE",
            "ALTER TABLE l3_gene_distribution_eval ADD COLUMN IF NOT EXISTS current_average_aged_prob DOUBLE",
            "ALTER TABLE l3_gene_distribution_eval ADD COLUMN IF NOT EXISTS current_average_remaining_vs_aged_odds DOUBLE",
            "ALTER TABLE l3_gene_distribution_eval ADD COLUMN IF NOT EXISTS current_average_aged_vs_remaining_odds DOUBLE",
        ]
        for sql in statements:
            self.conn.execute(sql)

    def _migrate_schema_v19_to_v20(self) -> None:
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS l3_gene_market_lifespan_surface (
                entity_scope                         VARCHAR NOT NULL,
                entity_code                          VARCHAR NOT NULL,
                calc_date                            DATE    NOT NULL,
                entity_name                          VARCHAR,
                source_table                         VARCHAR NOT NULL,
                price_source_kind                    VARCHAR NOT NULL,
                market_regime_direction              VARCHAR NOT NULL,
                market_regime_label                  VARCHAR NOT NULL,
                wave_role                            VARCHAR NOT NULL,
                surface_label                        VARCHAR NOT NULL,
                amplitude_metric_name                VARCHAR NOT NULL,
                history_reference_trade_days         INTEGER,
                sample_size                          INTEGER,
                sample_first_wave_start_date         DATE,
                sample_last_wave_end_date            DATE,
                amplitude_min                        DOUBLE,
                amplitude_mean                       DOUBLE,
                amplitude_q25                        DOUBLE,
                amplitude_q50                        DOUBLE,
                amplitude_q75                        DOUBLE,
                amplitude_p65                        DOUBLE,
                amplitude_p95                        DOUBLE,
                amplitude_max                        DOUBLE,
                duration_min                         DOUBLE,
                duration_mean                        DOUBLE,
                duration_q25                         DOUBLE,
                duration_q50                         DOUBLE,
                duration_q75                         DOUBLE,
                duration_p65                         DOUBLE,
                duration_p95                         DOUBLE,
                duration_max                         DOUBLE,
                current_wave_matches_surface         BOOLEAN,
                current_wave_direction               VARCHAR,
                current_wave_age_trade_days          INTEGER,
                current_wave_amplitude_value         DOUBLE,
                current_wave_amplitude_percentile    DOUBLE,
                current_wave_duration_percentile     DOUBLE,
                current_wave_joint_percentile        DOUBLE,
                current_wave_amplitude_band          VARCHAR,
                current_wave_duration_band           VARCHAR,
                current_wave_joint_band              VARCHAR,
                current_wave_average_remaining_prob  DOUBLE,
                current_wave_average_aged_prob       DOUBLE,
                current_wave_remaining_vs_aged_odds  DOUBLE,
                current_wave_aged_vs_remaining_odds  DOUBLE,
                created_at                           TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (entity_scope, entity_code, calc_date, surface_label)
            )
            """
        )

    def _migrate_schema_v6_to_v7(self) -> None:
        statements = [
            "ALTER TABLE l3_gene_wave ADD COLUMN IF NOT EXISTS turn_confirm_type VARCHAR",
            "ALTER TABLE l3_gene_wave ADD COLUMN IF NOT EXISTS turn_step1_date DATE",
            "ALTER TABLE l3_gene_wave ADD COLUMN IF NOT EXISTS turn_step2_date DATE",
            "ALTER TABLE l3_gene_wave ADD COLUMN IF NOT EXISTS turn_step3_date DATE",
            "ALTER TABLE l3_gene_wave ADD COLUMN IF NOT EXISTS two_b_confirm_type VARCHAR",
            "ALTER TABLE l3_gene_wave ADD COLUMN IF NOT EXISTS two_b_confirm_date DATE",
            "ALTER TABLE l3_gene_event ADD COLUMN IF NOT EXISTS event_family VARCHAR",
            "ALTER TABLE l3_gene_event ADD COLUMN IF NOT EXISTS structure_direction VARCHAR",
            "ALTER TABLE l3_gene_event ADD COLUMN IF NOT EXISTS anchor_wave_id VARCHAR",
            "ALTER TABLE l3_stock_gene ADD COLUMN IF NOT EXISTS latest_confirmed_turn_type VARCHAR",
            "ALTER TABLE l3_stock_gene ADD COLUMN IF NOT EXISTS latest_confirmed_turn_date DATE",
            "ALTER TABLE l3_stock_gene ADD COLUMN IF NOT EXISTS latest_two_b_confirm_type VARCHAR",
            "ALTER TABLE l3_stock_gene ADD COLUMN IF NOT EXISTS latest_two_b_confirm_date DATE",
        ]
        for sql in statements:
            self.conn.execute(sql)

    def _migrate_schema_v7_to_v8(self) -> None:
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS l3_gene_validation_eval (
                calc_date                           DATE    NOT NULL,
                metric_name                         VARCHAR NOT NULL,
                sample_scope                        VARCHAR NOT NULL,
                forward_horizon_trade_days          INTEGER NOT NULL,
                sample_size                         INTEGER,
                monotonicity_score                  DOUBLE,
                avg_daily_rank_corr                 DOUBLE,
                positive_daily_rank_corr_rate       DOUBLE,
                top_bucket_continuation_rate        DOUBLE,
                bottom_bucket_continuation_rate     DOUBLE,
                top_bucket_median_forward_return    DOUBLE,
                bottom_bucket_median_forward_return DOUBLE,
                top_bucket_median_forward_drawdown  DOUBLE,
                bottom_bucket_median_forward_drawdown DOUBLE,
                decision_tag                        VARCHAR,
                created_at                          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (
                    calc_date,
                    metric_name,
                    sample_scope,
                    forward_horizon_trade_days
                )
            )
            """
        )

    def _migrate_schema_v8_to_v9(self) -> None:
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS l3_gene_mirror (
                entity_scope                     VARCHAR NOT NULL,
                entity_code                      VARCHAR NOT NULL,
                calc_date                        DATE    NOT NULL,
                entity_name                      VARCHAR,
                source_table                     VARCHAR NOT NULL,
                price_source_kind                VARCHAR NOT NULL,
                current_wave_direction           VARCHAR,
                current_wave_role                VARCHAR,
                current_wave_start_date          DATE,
                current_wave_terminal_price      DOUBLE,
                current_wave_signed_return_pct   DOUBLE,
                current_wave_age_trade_days      INTEGER,
                current_wave_magnitude_pct       DOUBLE,
                current_wave_extreme_density     DOUBLE,
                current_wave_history_sample_size INTEGER,
                current_wave_magnitude_percentile DOUBLE,
                current_wave_duration_percentile DOUBLE,
                current_wave_extreme_density_percentile DOUBLE,
                current_wave_magnitude_band      VARCHAR,
                current_wave_duration_band       VARCHAR,
                current_wave_age_band            VARCHAR,
                latest_confirmed_turn_type       VARCHAR,
                latest_two_b_confirm_type        VARCHAR,
                gene_score                       DOUBLE,
                primary_ruler_metric             VARCHAR,
                primary_ruler_value              DOUBLE,
                primary_ruler_rank               INTEGER,
                primary_ruler_percentile         DOUBLE,
                mirror_gene_rank                 INTEGER,
                mirror_gene_percentile           DOUBLE,
                composite_decision_tag           VARCHAR,
                support_rise_ratio               DOUBLE,
                support_strong_ratio             DOUBLE,
                support_new_high_ratio           DOUBLE,
                support_amount_vs_ma20           DOUBLE,
                support_return_5d                DOUBLE,
                support_return_20d               DOUBLE,
                support_follow_through           DOUBLE,
                created_at                       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (entity_scope, entity_code, calc_date)
            )
            """
        )

    def _migrate_schema_v9_to_v10(self) -> None:
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS l3_gene_conditioning_eval (
                calc_date                         DATE    NOT NULL,
                signal_pattern                    VARCHAR NOT NULL,
                sample_scope                      VARCHAR NOT NULL,
                conditioning_key                  VARCHAR NOT NULL,
                conditioning_value                VARCHAR NOT NULL,
                sample_size                       INTEGER,
                hit_rate                          DOUBLE,
                avg_forward_return_pct            DOUBLE,
                median_forward_return_pct         DOUBLE,
                avg_mae_pct                       DOUBLE,
                avg_mfe_pct                       DOUBLE,
                hit_rate_delta_vs_pattern_baseline DOUBLE,
                payoff_delta_vs_pattern_baseline  DOUBLE,
                mae_delta_vs_pattern_baseline     DOUBLE,
                mfe_delta_vs_pattern_baseline     DOUBLE,
                edge_tag                          VARCHAR,
                created_at                        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (calc_date, signal_pattern, sample_scope, conditioning_key, conditioning_value)
            )
            """
        )

    def _migrate_schema_v10_to_v11(self) -> None:
        statements = [
            "ALTER TABLE l3_gene_wave ADD COLUMN IF NOT EXISTS trend_level VARCHAR",
            "ALTER TABLE l3_gene_wave ADD COLUMN IF NOT EXISTS context_trend_level VARCHAR",
            "ALTER TABLE l3_gene_wave ADD COLUMN IF NOT EXISTS context_trend_direction_before VARCHAR",
            "ALTER TABLE l3_gene_wave ADD COLUMN IF NOT EXISTS context_trend_direction_after VARCHAR",
            "ALTER TABLE l3_gene_wave ADD COLUMN IF NOT EXISTS wave_role_basis VARCHAR",
            "ALTER TABLE l3_stock_gene ADD COLUMN IF NOT EXISTS trend_level VARCHAR",
            "ALTER TABLE l3_stock_gene ADD COLUMN IF NOT EXISTS current_context_trend_level VARCHAR",
            "ALTER TABLE l3_stock_gene ADD COLUMN IF NOT EXISTS current_context_trend_direction VARCHAR",
            "ALTER TABLE l3_stock_gene ADD COLUMN IF NOT EXISTS current_wave_role_basis VARCHAR",
        ]
        for sql in statements:
            self.conn.execute(sql)

    def _ensure_optional_columns(self) -> None:
        """
        非破坏性 schema 演进：为已有库补齐报告扩展字段。
        这些列用于 Gate 诚信指标，不改变主键与核心执行语义。
        """
        optional_columns = [
            ("l1_stock_info", "list_status", "VARCHAR DEFAULT 'L'"),
            ("l4_daily_report", "reject_rate", "DOUBLE"),
            ("l4_daily_report", "missing_rate", "DOUBLE"),
            ("l4_daily_report", "exposure_rate", "DOUBLE"),
            ("l4_daily_report", "failure_reason_breakdown", "VARCHAR"),
            ("l4_daily_report", "opportunity_count", "INTEGER"),
            ("l4_daily_report", "filled_count", "INTEGER"),
            ("l4_daily_report", "skip_cash_count", "INTEGER"),
            ("l4_daily_report", "skip_maxpos_count", "INTEGER"),
            ("l4_daily_report", "participation_rate", "DOUBLE"),
            ("_meta_runs", "mode", "VARCHAR"),
            ("_meta_runs", "variant", "VARCHAR"),
            ("_meta_runs", "artifact_root", "VARCHAR"),
            ("l2_industry_daily", "amount_ma20", "DOUBLE"),
            ("l2_industry_daily", "return_5d", "DOUBLE"),
            ("l2_industry_daily", "return_20d", "DOUBLE"),
            ("l3_irs_daily", "rv_score", "DOUBLE"),
            ("l3_irs_daily", "rt_score", "DOUBLE"),
            ("l3_irs_daily", "bd_score", "DOUBLE"),
            ("l3_irs_daily", "gn_score", "DOUBLE"),
            ("l3_irs_daily", "rotation_status", "VARCHAR"),
            ("l3_irs_daily", "rotation_slope", "DOUBLE"),
            ("l3_signal_rank_exp", "pattern_strength", "DOUBLE"),
            ("selector_candidate_trace_exp", "candidate_reason", "VARCHAR"),
            ("selector_candidate_trace_exp", "coverage_flag", "VARCHAR"),
            ("selector_candidate_trace_exp", "source_snapshot_date", "DATE"),
            ("selector_candidate_trace_exp", "selected_for_pas", "BOOLEAN"),
            ("pas_trigger_trace_exp", "candidate_rank", "INTEGER"),
            ("pas_trigger_trace_exp", "selected_pattern", "VARCHAR"),
            ("pas_trigger_trace_exp", "detected", "BOOLEAN"),
            ("pas_trigger_trace_exp", "detect_reason", "VARCHAR"),
            ("pas_trigger_trace_exp", "pattern_strength", "DOUBLE"),
            ("pas_trigger_trace_exp", "pattern_quality_score", "DOUBLE"),
            ("pas_trigger_trace_exp", "quality_breakdown_json", "VARCHAR"),
            ("pas_trigger_trace_exp", "quality_status", "VARCHAR"),
            ("pas_trigger_trace_exp", "entry_ref", "DOUBLE"),
            ("pas_trigger_trace_exp", "stop_ref", "DOUBLE"),
            ("pas_trigger_trace_exp", "target_ref", "DOUBLE"),
            ("pas_trigger_trace_exp", "risk_reward_ref", "DOUBLE"),
            ("pas_trigger_trace_exp", "failure_handling_tag", "VARCHAR"),
            ("pas_trigger_trace_exp", "pattern_group", "VARCHAR"),
            ("pas_trigger_trace_exp", "registry_run_label", "VARCHAR"),
            ("pas_trigger_trace_exp", "reference_status", "VARCHAR"),
            ("pas_trigger_trace_exp", "trace_schema_version", "INTEGER"),
            ("pas_trigger_trace_exp", "trace_payload_json", "VARCHAR"),
            ("pas_trigger_trace_exp", "pattern_context_json", "VARCHAR"),
            ("l3_mss_daily", "market_coefficient_raw", "DOUBLE"),
            ("l3_mss_daily", "profit_effect_raw", "DOUBLE"),
            ("l3_mss_daily", "loss_effect_raw", "DOUBLE"),
            ("l3_mss_daily", "continuity_raw", "DOUBLE"),
            ("l3_mss_daily", "extreme_raw", "DOUBLE"),
            ("l3_mss_daily", "volatility_raw", "DOUBLE"),
            # Phase 3 / MSS 状态层：
            # 正式 DDL 在 _all_ddls 里定义，这里只负责给历史库补桥接列。
            ("l3_mss_daily", "phase", "VARCHAR"),
            ("l3_mss_daily", "phase_trend", "VARCHAR"),
            ("l3_mss_daily", "phase_days", "INTEGER"),
            ("l3_mss_daily", "position_advice", "VARCHAR"),
            ("l3_mss_daily", "risk_regime", "VARCHAR"),
            ("l3_mss_daily", "trend_quality", "VARCHAR"),
            ("irs_industry_trace_exp", "trace_scope", "VARCHAR DEFAULT 'SIGNAL_ATTACH'"),
            ("irs_industry_trace_exp", "industry_code", "VARCHAR"),
            ("irs_industry_trace_exp", "source_classification", "VARCHAR"),
            ("irs_industry_trace_exp", "benchmark_code", "VARCHAR"),
            ("irs_industry_trace_exp", "benchmark_pct", "DOUBLE"),
            ("irs_industry_trace_exp", "industry_pct_chg", "DOUBLE"),
            ("irs_industry_trace_exp", "amount", "DOUBLE"),
            ("irs_industry_trace_exp", "market_total_amount", "DOUBLE"),
            ("irs_industry_trace_exp", "amount_delta_10d", "DOUBLE"),
            ("irs_industry_trace_exp", "rs_raw", "DOUBLE"),
            ("irs_industry_trace_exp", "cf_raw", "DOUBLE"),
            ("irs_industry_trace_exp", "rs_score", "DOUBLE"),
            ("irs_industry_trace_exp", "cf_score", "DOUBLE"),
            ("irs_industry_trace_exp", "rv_score", "DOUBLE"),
            ("irs_industry_trace_exp", "rt_score", "DOUBLE"),
            ("irs_industry_trace_exp", "bd_score", "DOUBLE"),
            ("irs_industry_trace_exp", "gn_score", "DOUBLE"),
            ("irs_industry_trace_exp", "rotation_status", "VARCHAR"),
            ("irs_industry_trace_exp", "rotation_slope", "DOUBLE"),
            ("irs_industry_trace_exp", "industry_count_today", "INTEGER"),
            ("irs_industry_trace_exp", "rs_1d_raw", "DOUBLE"),
            ("irs_industry_trace_exp", "rs_5d_raw", "DOUBLE"),
            ("irs_industry_trace_exp", "rs_20d_raw", "DOUBLE"),
            ("irs_industry_trace_exp", "rank_stability_raw", "DOUBLE"),
            ("irs_industry_trace_exp", "flow_share", "DOUBLE"),
            ("irs_industry_trace_exp", "amount_vs_self_20d", "DOUBLE"),
            ("irs_industry_trace_exp", "strong_amount_share", "DOUBLE"),
            ("irs_industry_trace_exp", "top_rank_streak_5d", "INTEGER"),
            ("irs_industry_trace_exp", "momentum_consistency", "DOUBLE"),
            ("irs_industry_trace_exp", "industry_score", "DOUBLE"),
            ("irs_industry_trace_exp", "industry_rank", "INTEGER"),
            ("irs_industry_trace_exp", "coverage_flag", "VARCHAR"),
            ("mss_risk_overlay_trace_exp", "overlay_enabled", "BOOLEAN"),
            ("mss_risk_overlay_trace_exp", "ranker_mss_score", "DOUBLE"),
            ("mss_risk_overlay_trace_exp", "coverage_flag", "VARCHAR"),
            ("mss_risk_overlay_trace_exp", "market_coefficient_raw", "DOUBLE"),
            ("mss_risk_overlay_trace_exp", "profit_effect_raw", "DOUBLE"),
            ("mss_risk_overlay_trace_exp", "loss_effect_raw", "DOUBLE"),
            ("mss_risk_overlay_trace_exp", "continuity_raw", "DOUBLE"),
            ("mss_risk_overlay_trace_exp", "extreme_raw", "DOUBLE"),
            ("mss_risk_overlay_trace_exp", "volatility_raw", "DOUBLE"),
            ("mss_risk_overlay_trace_exp", "market_coefficient", "DOUBLE"),
            ("mss_risk_overlay_trace_exp", "profit_effect", "DOUBLE"),
            ("mss_risk_overlay_trace_exp", "loss_effect", "DOUBLE"),
            ("mss_risk_overlay_trace_exp", "continuity", "DOUBLE"),
            ("mss_risk_overlay_trace_exp", "extreme", "DOUBLE"),
            ("mss_risk_overlay_trace_exp", "volatility", "DOUBLE"),
            # overlay trace 的状态层字段同样先有正式 DDL，再由这里兼容旧库。
            ("mss_risk_overlay_trace_exp", "phase", "VARCHAR"),
            ("mss_risk_overlay_trace_exp", "phase_trend", "VARCHAR"),
            ("mss_risk_overlay_trace_exp", "phase_days", "INTEGER"),
            ("mss_risk_overlay_trace_exp", "position_advice", "VARCHAR"),
            ("mss_risk_overlay_trace_exp", "risk_regime", "VARCHAR"),
            ("mss_risk_overlay_trace_exp", "trend_quality", "VARCHAR"),
            ("mss_risk_overlay_trace_exp", "regime_source", "VARCHAR"),
            ("mss_risk_overlay_trace_exp", "overlay_reason", "VARCHAR"),
            ("mss_risk_overlay_trace_exp", "decision_bucket", "VARCHAR"),
            ("mss_risk_overlay_trace_exp", "target_max_positions", "INTEGER"),
            ("mss_risk_overlay_trace_exp", "max_positions_mode", "VARCHAR"),
            ("mss_risk_overlay_trace_exp", "max_positions_buffer_slots", "INTEGER"),
        ]
        # optional column 只允许补非主键、非执行语义列；
        # 一旦涉及 formal schema 或主流程字段变化，就应该走显式 migration，而不是这里静默补列。
        for table, col, typ in optional_columns:
            try:
                self.conn.execute(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {col} {typ}")
            except duckdb.Error:
                # 低版本 DuckDB 兼容：忽略 IF NOT EXISTS 不可用的失败。
                pass

    @staticmethod
    def _all_ddls() -> list[str]:
        return [
            # L1
            """
            CREATE TABLE IF NOT EXISTS l1_stock_daily (
                ts_code      VARCHAR NOT NULL,
                date         DATE    NOT NULL,
                open         DOUBLE,
                high         DOUBLE,
                low          DOUBLE,
                close        DOUBLE,
                pre_close    DOUBLE,
                volume       DOUBLE,
                amount       DOUBLE,
                pct_chg      DOUBLE,
                adj_factor   DOUBLE,
                is_halt      BOOLEAN DEFAULT FALSE,
                up_limit     DOUBLE,
                down_limit   DOUBLE,
                total_mv     DOUBLE,
                circ_mv      DOUBLE,
                PRIMARY KEY (ts_code, date)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS l1_index_daily (
                ts_code      VARCHAR NOT NULL,
                date         DATE    NOT NULL,
                open         DOUBLE,
                high         DOUBLE,
                low          DOUBLE,
                close        DOUBLE,
                pre_close    DOUBLE,
                pct_chg      DOUBLE,
                volume       DOUBLE,
                amount       DOUBLE,
                PRIMARY KEY (ts_code, date)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS l1_stock_info (
                ts_code        VARCHAR NOT NULL,
                name           VARCHAR,
                industry       VARCHAR,
                market         VARCHAR,
                list_status    VARCHAR DEFAULT 'L',
                is_st          BOOLEAN DEFAULT FALSE,
                list_date      DATE,
                effective_from DATE NOT NULL,
                PRIMARY KEY (ts_code, effective_from)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS l1_industry_member (
                industry_code     VARCHAR NOT NULL,
                industry_name     VARCHAR NOT NULL,
                ts_code           VARCHAR NOT NULL,
                in_date           DATE    NOT NULL,
                out_date          DATE,
                is_new            VARCHAR,
                source_trade_date DATE,
                PRIMARY KEY (industry_code, ts_code, in_date)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS l1_trade_calendar (
                date           DATE NOT NULL PRIMARY KEY,
                is_trade_day   BOOLEAN NOT NULL,
                prev_trade_day DATE,
                next_trade_day DATE
            )
            """,
            # L2
            """
            CREATE TABLE IF NOT EXISTS l2_stock_adj_daily (
                code         VARCHAR NOT NULL,
                date         DATE    NOT NULL,
                adj_open     DOUBLE,
                adj_high     DOUBLE,
                adj_low      DOUBLE,
                adj_close    DOUBLE,
                volume       DOUBLE,
                amount       DOUBLE,
                pct_chg      DOUBLE,
                ma5          DOUBLE,
                ma10         DOUBLE,
                ma20         DOUBLE,
                ma60         DOUBLE,
                volume_ma5   DOUBLE,
                volume_ma20  DOUBLE,
                volume_ratio DOUBLE,
                PRIMARY KEY (code, date)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS l2_industry_daily (
                industry    VARCHAR NOT NULL,
                date        DATE    NOT NULL,
                pct_chg     DOUBLE,
                amount      DOUBLE,
                stock_count INTEGER,
                rise_count  INTEGER,
                fall_count  INTEGER,
                amount_ma20 DOUBLE,
                return_5d   DOUBLE,
                return_20d  DOUBLE,
                PRIMARY KEY (industry, date)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS l2_industry_structure_daily (
                industry                  VARCHAR NOT NULL,
                date                      DATE    NOT NULL,
                strong_up_count           INTEGER,
                new_high_count            INTEGER,
                leader_count              INTEGER,
                leader_strength           DOUBLE,
                strong_stock_ratio        DOUBLE,
                strong_stock_amount_share DOUBLE,
                leader_follow_through     DOUBLE,
                bof_hit_density_5d        DOUBLE,
                PRIMARY KEY (industry, date)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS l2_market_snapshot (
                date                        DATE NOT NULL PRIMARY KEY,
                total_stocks                INTEGER,
                rise_count                  INTEGER,
                fall_count                  INTEGER,
                strong_up_count             INTEGER,
                strong_down_count           INTEGER,
                limit_up_count              INTEGER,
                limit_down_count            INTEGER,
                touched_limit_up_count      INTEGER,
                new_100d_high_count         INTEGER,
                new_100d_low_count          INTEGER,
                continuous_limit_up_2d      INTEGER,
                continuous_limit_up_3d_plus INTEGER,
                continuous_new_high_2d_plus INTEGER,
                high_open_low_close_count   INTEGER,
                low_open_high_close_count   INTEGER,
                pct_chg_std                 DOUBLE,
                amount_volatility           DOUBLE
            )
            """,
            # L3
            """
            CREATE TABLE IF NOT EXISTS l3_mss_daily (
                -- l3_mss_daily 是市场层正式真相源：
                -- score/signal 是兼容结果，phase/risk_regime 是 Phase 3 新增状态层，
                -- Broker 必须能只读这张表就拿到当天正式市场状态。
                date               DATE NOT NULL PRIMARY KEY,
                score              DOUBLE,
                signal             VARCHAR,
                market_coefficient_raw DOUBLE,
                profit_effect_raw      DOUBLE,
                loss_effect_raw        DOUBLE,
                continuity_raw         DOUBLE,
                extreme_raw            DOUBLE,
                volatility_raw         DOUBLE,
                market_coefficient DOUBLE,
                profit_effect      DOUBLE,
                loss_effect        DOUBLE,
                continuity         DOUBLE,
                extreme            DOUBLE,
                volatility         DOUBLE,
                phase              VARCHAR,
                phase_trend        VARCHAR,
                phase_days         INTEGER,
                position_advice    VARCHAR,
                risk_regime        VARCHAR,
                trend_quality      VARCHAR
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS l3_irs_daily (
                date      DATE    NOT NULL,
                industry  VARCHAR NOT NULL,
                score     DOUBLE,
                rank      INTEGER,
                rs_score  DOUBLE,
                cf_score  DOUBLE,
                rv_score  DOUBLE,
                rt_score  DOUBLE,
                bd_score  DOUBLE,
                gn_score  DOUBLE,
                rotation_status VARCHAR,
                rotation_slope  DOUBLE,
                PRIMARY KEY (date, industry)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS l3_signals (
                -- l3_signals 只保留“最近一次 formal Signal 输出”的兼容缓存。
                -- 它不是 run-isolated 真相源；跨 run 对比与归因必须读取 l3_signal_rank_exp + trace 表。
                signal_id   VARCHAR NOT NULL PRIMARY KEY,
                code        VARCHAR NOT NULL,
                signal_date DATE    NOT NULL,
                action      VARCHAR NOT NULL,
                strength    DOUBLE,
                pattern     VARCHAR NOT NULL,
                reason_code VARCHAR,
                created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS l3_signal_rank_exp (
                -- rank_exp 是 DTT 正式实验真相源：run_id 隔离、排序结果可回放、可与 trace 链拼接。
                run_id       VARCHAR NOT NULL,
                signal_id    VARCHAR NOT NULL,
                signal_date  DATE    NOT NULL,
                code         VARCHAR NOT NULL,
                industry     VARCHAR,
                variant      VARCHAR NOT NULL,
                pattern_strength DOUBLE NOT NULL,
                irs_score    DOUBLE NOT NULL,
                mss_score    DOUBLE NOT NULL,
                final_score  DOUBLE NOT NULL,
                final_rank   INTEGER NOT NULL,
                selected     BOOLEAN NOT NULL,
                created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (run_id, signal_id)
            )
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_signals_date_code
            ON l3_signals(signal_date, code)
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_signal_rank_exp_run_rank
            ON l3_signal_rank_exp(run_id, final_rank)
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_signal_rank_exp_signal
            ON l3_signal_rank_exp(signal_id)
            """,
            """
            CREATE TABLE IF NOT EXISTS selector_candidate_trace_exp (
                -- Selector 的真相源：解释“为什么入选 / 为什么被漏斗挡住”。
                run_id               VARCHAR NOT NULL,
                signal_date          DATE    NOT NULL,
                code                 VARCHAR NOT NULL,
                pipeline_mode        VARCHAR NOT NULL,
                preselect_score_mode VARCHAR,
                industry             VARCHAR,
                amount               DOUBLE,
                volume_ratio         DOUBLE,
                filters_passed       VARCHAR,
                reject_reason        VARCHAR,
                candidate_reason     VARCHAR,
                coverage_flag        VARCHAR,
                source_snapshot_date DATE,
                liquidity_tag        VARCHAR,
                preselect_score      DOUBLE,
                final_score          DOUBLE,
                candidate_rank       INTEGER,
                candidate_top_n      INTEGER,
                selected             BOOLEAN NOT NULL,
                selected_for_pas     BOOLEAN,
                created_at           TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (run_id, signal_date, code)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS pas_trigger_trace_exp (
                -- PAS 的真相源：保留 detector 触发/未触发、组合仲裁和 sidecar 解释层。
                run_id                VARCHAR NOT NULL,
                signal_date           DATE    NOT NULL,
                code                  VARCHAR NOT NULL,
                detector              VARCHAR NOT NULL,
                signal_id             VARCHAR,
                pattern               VARCHAR,
                candidate_rank        INTEGER,
                selected_pattern      VARCHAR,
                active_detector_count INTEGER,
                combination_mode      VARCHAR,
                history_days          INTEGER,
                min_history_days      INTEGER,
                triggered             BOOLEAN NOT NULL,
                detected              BOOLEAN,
                skip_reason           VARCHAR,
                detect_reason         VARCHAR,
                reason_code           VARCHAR,
                strength              DOUBLE,
                pattern_strength      DOUBLE,
                bof_strength          DOUBLE,
                lower_bound           DOUBLE,
                today_low             DOUBLE,
                today_close           DOUBLE,
                today_open            DOUBLE,
                today_high            DOUBLE,
                close_pos             DOUBLE,
                volume                DOUBLE,
                volume_ma20           DOUBLE,
                volume_ratio          DOUBLE,
                cond_break            BOOLEAN,
                cond_recover          BOOLEAN,
                cond_close_pos        BOOLEAN,
                cond_volume           BOOLEAN,
                pattern_quality_score DOUBLE,
                quality_breakdown_json VARCHAR,
                quality_status        VARCHAR,
                entry_ref             DOUBLE,
                stop_ref              DOUBLE,
                target_ref            DOUBLE,
                risk_reward_ref       DOUBLE,
                failure_handling_tag  VARCHAR,
                pattern_group         VARCHAR,
                registry_run_label    VARCHAR,
                reference_status      VARCHAR,
                trace_schema_version  INTEGER,
                trace_payload_json    VARCHAR,
                pattern_context_json  VARCHAR,
                created_at            TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (run_id, signal_date, code, detector)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS irs_industry_trace_exp (
                -- IRS 真相源拆成两层：行业日排名本身，以及 signal attach 后的解释记录。
                run_id            VARCHAR NOT NULL,
                signal_id         VARCHAR NOT NULL,
                signal_date       DATE    NOT NULL,
                code              VARCHAR NOT NULL,
                industry          VARCHAR,
                variant           VARCHAR NOT NULL,
                uses_irs          BOOLEAN NOT NULL,
                daily_score       DOUBLE,
                daily_rank        INTEGER,
                signal_irs_score  DOUBLE NOT NULL,
                fill_score        DOUBLE NOT NULL,
                status            VARCHAR NOT NULL,
                trace_scope       VARCHAR DEFAULT 'SIGNAL_ATTACH',
                industry_code     VARCHAR,
                source_classification VARCHAR,
                benchmark_code    VARCHAR,
                benchmark_pct     DOUBLE,
                industry_pct_chg  DOUBLE,
                amount            DOUBLE,
                market_total_amount DOUBLE,
                amount_delta_10d  DOUBLE,
                rs_raw            DOUBLE,
                cf_raw            DOUBLE,
                rs_score          DOUBLE,
                cf_score          DOUBLE,
                rv_score          DOUBLE,
                rt_score          DOUBLE,
                bd_score          DOUBLE,
                gn_score          DOUBLE,
                rotation_status   VARCHAR,
                rotation_slope    DOUBLE,
                industry_count_today INTEGER,
                rs_1d_raw         DOUBLE,
                rs_5d_raw         DOUBLE,
                rs_20d_raw        DOUBLE,
                rank_stability_raw DOUBLE,
                flow_share        DOUBLE,
                amount_vs_self_20d DOUBLE,
                strong_amount_share DOUBLE,
                top_rank_streak_5d INTEGER,
                momentum_consistency DOUBLE,
                industry_score    DOUBLE,
                industry_rank     INTEGER,
                coverage_flag     VARCHAR,
                created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (run_id, signal_id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS mss_risk_overlay_trace_exp (
                -- MSS 在当前主线主要服务 Broker，这张表记录的是执行层看到的 overlay 结果。
                -- 这里必须同时保留：
                -- 1. 兼容 signal / score
                -- 2. Phase 3 正式状态层 phase / trend / regime
                -- 3. fallback 与决策归因 overlay_reason / decision_bucket
                run_id                         VARCHAR NOT NULL,
                signal_id                      VARCHAR NOT NULL,
                signal_date                    DATE    NOT NULL,
                code                           VARCHAR NOT NULL,
                pattern                        VARCHAR NOT NULL,
                variant                        VARCHAR,
                signal_mss_score               DOUBLE,
                ranker_mss_score               DOUBLE,
                overlay_enabled                BOOLEAN,
                overlay_state                  VARCHAR NOT NULL,
                coverage_flag                  VARCHAR,
                market_signal                  VARCHAR NOT NULL,
                market_score                   DOUBLE NOT NULL,
                market_coefficient_raw         DOUBLE,
                profit_effect_raw              DOUBLE,
                loss_effect_raw                DOUBLE,
                continuity_raw                 DOUBLE,
                extreme_raw                    DOUBLE,
                volatility_raw                 DOUBLE,
                market_coefficient             DOUBLE,
                profit_effect                  DOUBLE,
                loss_effect                    DOUBLE,
                continuity                     DOUBLE,
                extreme                        DOUBLE,
                volatility                     DOUBLE,
                phase                          VARCHAR,
                phase_trend                    VARCHAR,
                phase_days                     INTEGER,
                position_advice                VARCHAR,
                risk_regime                    VARCHAR,
                trend_quality                  VARCHAR,
                regime_source                  VARCHAR,
                overlay_reason                 VARCHAR,
                base_max_positions             INTEGER NOT NULL,
                base_risk_per_trade_pct        DOUBLE NOT NULL,
                base_max_position_pct          DOUBLE NOT NULL,
                max_positions_mult             DOUBLE NOT NULL,
                risk_per_trade_mult            DOUBLE NOT NULL,
                max_position_mult              DOUBLE NOT NULL,
                target_max_positions           INTEGER,
                effective_max_positions        INTEGER NOT NULL,
                max_positions_mode             VARCHAR,
                max_positions_buffer_slots     INTEGER,
                effective_risk_per_trade_pct   DOUBLE NOT NULL,
                effective_max_position_pct     DOUBLE NOT NULL,
                holdings_before                INTEGER NOT NULL,
                available_cash                 DOUBLE NOT NULL,
                portfolio_market_value         DOUBLE NOT NULL,
                decision_status                VARCHAR NOT NULL,
                decision_bucket                VARCHAR,
                decision_reason                VARCHAR,
                reserved_cash                  DOUBLE NOT NULL,
                created_at                     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (run_id, signal_id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS l3_stock_gene (
                code            VARCHAR NOT NULL,
                calc_date       DATE    NOT NULL,
                bull_score      DOUBLE,
                bear_score      DOUBLE,
                gene_score      DOUBLE,
                limit_up_freq   DOUBLE,
                streak_up_avg   DOUBLE,
                new_high_freq   DOUBLE,
                strength_ratio  DOUBLE,
                resilience      DOUBLE,
                limit_down_freq DOUBLE,
                streak_down_avg DOUBLE,
                new_low_freq    DOUBLE,
                weakness_ratio  DOUBLE,
                fragility       DOUBLE,
                trend_level VARCHAR,
                trend_direction VARCHAR,
                current_wave_id VARCHAR,
                current_wave_direction VARCHAR,
                current_context_trend_level VARCHAR,
                current_context_trend_direction VARCHAR,
                current_context_view_scope VARCHAR,
                current_context_view_level VARCHAR,
                current_context_parent_trend_level VARCHAR,
                current_context_parent_trend_direction VARCHAR,
                current_wave_role VARCHAR,
                current_wave_role_basis VARCHAR,
                reversal_state VARCHAR,
                reversal_state_family VARCHAR,
                reversal_state_is_confirmed_turn BOOLEAN,
                reversal_state_is_two_b_watch BOOLEAN,
                reversal_state_is_countertrend_watch BOOLEAN,
                latest_completed_reversal_tag VARCHAR,
                current_wave_start_date DATE,
                current_wave_reference_price DOUBLE,
                current_wave_terminal_price DOUBLE,
                current_wave_age_trade_days INTEGER,
                current_wave_signed_return_pct DOUBLE,
                current_wave_magnitude_pct DOUBLE,
                current_wave_extreme_count INTEGER,
                current_wave_extreme_density DOUBLE,
                current_wave_last_extreme_seq INTEGER,
                current_wave_last_extreme_date DATE,
                current_wave_last_extreme_price DOUBLE,
                current_wave_two_b_failure_count INTEGER,
                current_wave_history_sample_size INTEGER,
                current_wave_history_reference_trade_days INTEGER,
                current_wave_history_span_trade_days INTEGER,
                current_wave_magnitude_rank INTEGER,
                current_wave_duration_rank INTEGER,
                current_wave_extreme_density_rank INTEGER,
                current_wave_magnitude_percentile DOUBLE,
                current_wave_duration_percentile DOUBLE,
                current_wave_extreme_density_percentile DOUBLE,
                current_wave_lifespan_joint_percentile DOUBLE,
                current_wave_magnitude_zscore DOUBLE,
                current_wave_duration_zscore DOUBLE,
                current_wave_extreme_density_zscore DOUBLE,
                current_wave_magnitude_remaining_prob DOUBLE,
                current_wave_duration_remaining_prob DOUBLE,
                current_wave_lifespan_average_remaining_prob DOUBLE,
                current_wave_lifespan_average_aged_prob DOUBLE,
                current_wave_lifespan_remaining_vs_aged_odds DOUBLE,
                current_wave_lifespan_aged_vs_remaining_odds DOUBLE,
                current_wave_magnitude_q25 DOUBLE,
                current_wave_magnitude_q50 DOUBLE,
                current_wave_magnitude_q75 DOUBLE,
                current_wave_magnitude_p65 DOUBLE,
                current_wave_magnitude_p95 DOUBLE,
                current_wave_magnitude_band VARCHAR,
                current_wave_duration_q25 DOUBLE,
                current_wave_duration_q50 DOUBLE,
                current_wave_duration_q75 DOUBLE,
                current_wave_duration_p65 DOUBLE,
                current_wave_duration_p95 DOUBLE,
                current_wave_duration_band VARCHAR,
                current_wave_age_band VARCHAR,
                current_wave_age_band_basis VARCHAR,
                current_wave_lifespan_joint_band VARCHAR,
                current_wave_prior_mainstream_wave_id VARCHAR,
                current_wave_prior_mainstream_magnitude_pct DOUBLE,
                current_wave_retracement_vs_prior_mainstream_pct DOUBLE,
                latest_confirmed_turn_type VARCHAR,
                latest_confirmed_turn_date DATE,
                latest_two_b_confirm_type VARCHAR,
                latest_two_b_confirm_date DATE,
                current_two_b_window_bars INTEGER,
                current_two_b_window_basis VARCHAR,
                current_short_trend_level VARCHAR,
                current_short_wave_id VARCHAR,
                current_short_wave_direction VARCHAR,
                current_short_context_trend_level VARCHAR,
                current_short_context_trend_direction VARCHAR,
                current_short_wave_role VARCHAR,
                current_short_wave_role_basis VARCHAR,
                current_short_two_b_window_bars INTEGER,
                current_short_two_b_window_basis VARCHAR,
                current_short_wave_start_date DATE,
                current_short_wave_age_trade_days INTEGER,
                current_intermediate_trend_level VARCHAR,
                current_intermediate_wave_id VARCHAR,
                current_intermediate_wave_direction VARCHAR,
                current_intermediate_context_trend_level VARCHAR,
                current_intermediate_context_trend_direction VARCHAR,
                current_intermediate_wave_role VARCHAR,
                current_intermediate_wave_role_basis VARCHAR,
                current_intermediate_two_b_window_bars INTEGER,
                current_intermediate_two_b_window_basis VARCHAR,
                current_intermediate_wave_start_date DATE,
                current_intermediate_wave_age_trade_days INTEGER,
                current_long_trend_level VARCHAR,
                current_long_wave_id VARCHAR,
                current_long_wave_direction VARCHAR,
                current_long_context_trend_level VARCHAR,
                current_long_context_trend_direction VARCHAR,
                current_long_wave_role VARCHAR,
                current_long_wave_role_basis VARCHAR,
                current_long_two_b_window_bars INTEGER,
                current_long_two_b_window_basis VARCHAR,
                current_long_wave_start_date DATE,
                current_long_wave_age_trade_days INTEGER,
                cross_section_magnitude_rank INTEGER,
                cross_section_magnitude_percentile DOUBLE,
                cross_section_duration_rank INTEGER,
                cross_section_duration_percentile DOUBLE,
                cross_section_extreme_density_rank INTEGER,
                cross_section_extreme_density_percentile DOUBLE,
                PRIMARY KEY (code, calc_date)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS l3_gene_wave (
                code                        VARCHAR NOT NULL,
                wave_id                     VARCHAR NOT NULL,
                direction                   VARCHAR,
                start_date                  DATE,
                end_date                    DATE,
                start_price                 DOUBLE,
                end_price                   DOUBLE,
                signed_return_pct           DOUBLE,
                magnitude_pct               DOUBLE,
                duration_trade_days         INTEGER,
                extreme_count               INTEGER,
                extreme_density             DOUBLE,
                last_extreme_date           DATE,
                last_extreme_price          DOUBLE,
                two_b_failure_count         INTEGER,
                end_confirm_index           INTEGER,
                trend_level                 VARCHAR,
                trend_direction_before      VARCHAR,
                trend_direction_after       VARCHAR,
                context_trend_level         VARCHAR,
                context_trend_direction_before VARCHAR,
                context_trend_direction_after VARCHAR,
                wave_role                   VARCHAR,
                wave_role_basis             VARCHAR,
                reversal_tag                VARCHAR,
                history_sample_size         INTEGER,
                history_reference_trade_days INTEGER,
                history_span_trade_days     INTEGER,
                magnitude_rank              INTEGER,
                duration_rank               INTEGER,
                extreme_density_rank        INTEGER,
                magnitude_percentile        DOUBLE,
                duration_percentile         DOUBLE,
                extreme_density_percentile  DOUBLE,
                lifespan_joint_percentile   DOUBLE,
                magnitude_zscore            DOUBLE,
                duration_zscore             DOUBLE,
                extreme_density_zscore      DOUBLE,
                magnitude_remaining_prob    DOUBLE,
                duration_remaining_prob     DOUBLE,
                lifespan_average_remaining_prob DOUBLE,
                lifespan_average_aged_prob  DOUBLE,
                lifespan_remaining_vs_aged_odds DOUBLE,
                lifespan_aged_vs_remaining_odds DOUBLE,
                magnitude_q25               DOUBLE,
                magnitude_q50               DOUBLE,
                magnitude_q75               DOUBLE,
                magnitude_p65               DOUBLE,
                magnitude_p95               DOUBLE,
                magnitude_band              VARCHAR,
                duration_q25                DOUBLE,
                duration_q50                DOUBLE,
                duration_q75                DOUBLE,
                duration_p65                DOUBLE,
                duration_p95                DOUBLE,
                duration_band               VARCHAR,
                wave_age_band               VARCHAR,
                wave_age_band_basis         VARCHAR,
                lifespan_joint_band         VARCHAR,
                prior_mainstream_wave_id    VARCHAR,
                prior_mainstream_magnitude_pct DOUBLE,
                retracement_vs_prior_mainstream_pct DOUBLE,
                turn_confirm_type           VARCHAR,
                turn_step1_date             DATE,
                turn_step2_date             DATE,
                turn_step3_date             DATE,
                turn_step1_condition        VARCHAR,
                turn_step2_condition        VARCHAR,
                turn_step3_condition        VARCHAR,
                two_b_confirm_type          VARCHAR,
                two_b_confirm_date          DATE,
                two_b_window_bars           INTEGER,
                two_b_window_basis          VARCHAR,
                created_at                  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (code, wave_id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS l3_gene_event (
                code                    VARCHAR NOT NULL,
                wave_id                 VARCHAR NOT NULL,
                event_date              DATE    NOT NULL,
                event_seq               INTEGER NOT NULL,
                direction               VARCHAR,
                event_type              VARCHAR,
                event_price             DOUBLE,
                previous_extreme_price  DOUBLE,
                spacing_trade_days      INTEGER,
                density_after_event     DOUBLE,
                is_two_b_failure        BOOLEAN,
                failure_date            DATE,
                confirmation_window_bars INTEGER,
                confirmation_window_basis VARCHAR,
                structure_condition     VARCHAR,
                event_family            VARCHAR,
                structure_direction     VARCHAR,
                anchor_wave_id          VARCHAR,
                created_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (code, wave_id, event_seq)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS l3_gene_factor_eval (
                calc_date                   DATE    NOT NULL,
                factor_name                 VARCHAR NOT NULL,
                sample_scope                VARCHAR NOT NULL,
                direction_scope             VARCHAR NOT NULL,
                forward_horizon_trade_days  INTEGER NOT NULL,
                bin_method                  VARCHAR NOT NULL,
                bin_label                   VARCHAR NOT NULL,
                sample_size                 INTEGER,
                continuation_rate           DOUBLE,
                reversal_rate               DOUBLE,
                median_forward_return       DOUBLE,
                median_forward_drawdown     DOUBLE,
                monotonicity_score          DOUBLE,
                created_at                  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (
                    calc_date,
                    factor_name,
                    sample_scope,
                    direction_scope,
                    forward_horizon_trade_days,
                    bin_label
                )
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS l3_gene_distribution_eval (
                code                       VARCHAR NOT NULL,
                calc_date                  DATE    NOT NULL,
                current_wave_id            VARCHAR NOT NULL,
                direction                  VARCHAR NOT NULL,
                metric_name                VARCHAR NOT NULL,
                sample_scope               VARCHAR NOT NULL,
                band_method                VARCHAR NOT NULL,
                history_sample_size        INTEGER,
                band_sample_size           INTEGER,
                current_value              DOUBLE,
                current_percentile         DOUBLE,
                current_metric_remaining_prob DOUBLE,
                current_metric_aged_prob   DOUBLE,
                current_average_remaining_prob DOUBLE,
                current_average_aged_prob  DOUBLE,
                current_average_remaining_vs_aged_odds DOUBLE,
                current_average_aged_vs_remaining_odds DOUBLE,
                threshold_q25              DOUBLE,
                threshold_q50              DOUBLE,
                threshold_q75              DOUBLE,
                threshold_p65              DOUBLE,
                threshold_p95              DOUBLE,
                band_label                 VARCHAR,
                continuation_base_rate     DOUBLE,
                reversal_base_rate         DOUBLE,
                median_forward_return      DOUBLE,
                median_forward_drawdown    DOUBLE,
                created_at                 TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (code, calc_date, metric_name)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS l3_gene_validation_eval (
                calc_date                           DATE    NOT NULL,
                metric_name                         VARCHAR NOT NULL,
                sample_scope                        VARCHAR NOT NULL,
                forward_horizon_trade_days          INTEGER NOT NULL,
                sample_size                         INTEGER,
                monotonicity_score                  DOUBLE,
                avg_daily_rank_corr                 DOUBLE,
                positive_daily_rank_corr_rate       DOUBLE,
                top_bucket_continuation_rate        DOUBLE,
                bottom_bucket_continuation_rate     DOUBLE,
                top_bucket_median_forward_return    DOUBLE,
                bottom_bucket_median_forward_return DOUBLE,
                top_bucket_median_forward_drawdown  DOUBLE,
                bottom_bucket_median_forward_drawdown DOUBLE,
                decision_tag                        VARCHAR,
                created_at                          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (
                    calc_date,
                    metric_name,
                    sample_scope,
                    forward_horizon_trade_days
                )
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS l3_gene_mirror (
                entity_scope                     VARCHAR NOT NULL,
                entity_code                      VARCHAR NOT NULL,
                calc_date                        DATE    NOT NULL,
                entity_name                      VARCHAR,
                source_table                     VARCHAR NOT NULL,
                price_source_kind                VARCHAR NOT NULL,
                current_wave_direction           VARCHAR,
                current_wave_role                VARCHAR,
                current_wave_start_date          DATE,
                current_wave_terminal_price      DOUBLE,
                current_wave_signed_return_pct   DOUBLE,
                current_wave_age_trade_days      INTEGER,
                current_wave_magnitude_pct       DOUBLE,
                current_wave_extreme_density     DOUBLE,
                current_wave_history_sample_size INTEGER,
                current_wave_magnitude_percentile DOUBLE,
                current_wave_duration_percentile DOUBLE,
                current_wave_extreme_density_percentile DOUBLE,
                current_wave_magnitude_band      VARCHAR,
                current_wave_duration_band       VARCHAR,
                current_wave_age_band            VARCHAR,
                latest_confirmed_turn_type       VARCHAR,
                latest_two_b_confirm_type        VARCHAR,
                gene_score                       DOUBLE,
                primary_ruler_metric             VARCHAR,
                primary_ruler_value              DOUBLE,
                primary_ruler_rank               INTEGER,
                primary_ruler_percentile         DOUBLE,
                mirror_gene_rank                 INTEGER,
                mirror_gene_percentile           DOUBLE,
                composite_decision_tag           VARCHAR,
                support_rise_ratio               DOUBLE,
                support_strong_ratio             DOUBLE,
                support_new_high_ratio           DOUBLE,
                support_amount_vs_ma20           DOUBLE,
                support_return_5d                DOUBLE,
                support_return_20d               DOUBLE,
                support_follow_through           DOUBLE,
                created_at                       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (entity_scope, entity_code, calc_date)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS l3_gene_market_lifespan_surface (
                entity_scope                         VARCHAR NOT NULL,
                entity_code                          VARCHAR NOT NULL,
                calc_date                            DATE    NOT NULL,
                entity_name                          VARCHAR,
                source_table                         VARCHAR NOT NULL,
                price_source_kind                    VARCHAR NOT NULL,
                market_regime_direction              VARCHAR NOT NULL,
                market_regime_label                  VARCHAR NOT NULL,
                wave_role                            VARCHAR NOT NULL,
                surface_label                        VARCHAR NOT NULL,
                amplitude_metric_name                VARCHAR NOT NULL,
                history_reference_trade_days         INTEGER,
                sample_size                          INTEGER,
                sample_first_wave_start_date         DATE,
                sample_last_wave_end_date            DATE,
                amplitude_min                        DOUBLE,
                amplitude_mean                       DOUBLE,
                amplitude_q25                        DOUBLE,
                amplitude_q50                        DOUBLE,
                amplitude_q75                        DOUBLE,
                amplitude_p65                        DOUBLE,
                amplitude_p95                        DOUBLE,
                amplitude_max                        DOUBLE,
                duration_min                         DOUBLE,
                duration_mean                        DOUBLE,
                duration_q25                         DOUBLE,
                duration_q50                         DOUBLE,
                duration_q75                         DOUBLE,
                duration_p65                         DOUBLE,
                duration_p95                         DOUBLE,
                duration_max                         DOUBLE,
                current_wave_matches_surface         BOOLEAN,
                current_wave_direction               VARCHAR,
                current_wave_age_trade_days          INTEGER,
                current_wave_amplitude_value         DOUBLE,
                current_wave_amplitude_percentile    DOUBLE,
                current_wave_duration_percentile     DOUBLE,
                current_wave_joint_percentile        DOUBLE,
                current_wave_amplitude_band          VARCHAR,
                current_wave_duration_band           VARCHAR,
                current_wave_joint_band              VARCHAR,
                current_wave_average_remaining_prob  DOUBLE,
                current_wave_average_aged_prob       DOUBLE,
                current_wave_remaining_vs_aged_odds  DOUBLE,
                current_wave_aged_vs_remaining_odds  DOUBLE,
                created_at                           TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (entity_scope, entity_code, calc_date, surface_label)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS l3_gene_conditioning_eval (
                calc_date                         DATE    NOT NULL,
                signal_pattern                    VARCHAR NOT NULL,
                sample_scope                      VARCHAR NOT NULL,
                conditioning_key                  VARCHAR NOT NULL,
                conditioning_value                VARCHAR NOT NULL,
                sample_size                       INTEGER,
                hit_rate                          DOUBLE,
                avg_forward_return_pct            DOUBLE,
                median_forward_return_pct         DOUBLE,
                avg_mae_pct                       DOUBLE,
                avg_mfe_pct                       DOUBLE,
                hit_rate_delta_vs_pattern_baseline DOUBLE,
                payoff_delta_vs_pattern_baseline  DOUBLE,
                mae_delta_vs_pattern_baseline     DOUBLE,
                mfe_delta_vs_pattern_baseline     DOUBLE,
                edge_tag                          VARCHAR,
                created_at                        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (calc_date, signal_pattern, sample_scope, conditioning_key, conditioning_value)
            )
            """,
            # L4
            """
            CREATE TABLE IF NOT EXISTS l4_orders (
                order_id      VARCHAR NOT NULL PRIMARY KEY,
                signal_id     VARCHAR NOT NULL,
                code          VARCHAR NOT NULL,
                action        VARCHAR NOT NULL,
                pattern       VARCHAR NOT NULL,
                quantity      INTEGER,
                price_limit   DOUBLE,
                execute_date  DATE NOT NULL,
                is_paper      BOOLEAN DEFAULT FALSE,
                status        VARCHAR DEFAULT 'PENDING',
                reject_reason VARCHAR,
                position_id   VARCHAR,
                exit_plan_id  VARCHAR,
                exit_leg_id   VARCHAR,
                exit_leg_seq  INTEGER,
                exit_leg_count INTEGER,
                exit_reason_code VARCHAR,
                is_partial_exit BOOLEAN DEFAULT FALSE,
                remaining_qty_before INTEGER,
                target_qty_after INTEGER,
                created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS l4_trades (
                trade_id      VARCHAR NOT NULL PRIMARY KEY,
                order_id      VARCHAR NOT NULL,
                code          VARCHAR NOT NULL,
                execute_date  DATE NOT NULL,
                action        VARCHAR NOT NULL,
                pattern       VARCHAR NOT NULL,
                price         DOUBLE,
                quantity      INTEGER,
                fee           DOUBLE,
                slippage_bps  DOUBLE DEFAULT 0,
                is_paper      BOOLEAN DEFAULT FALSE,
                position_id   VARCHAR,
                exit_plan_id  VARCHAR,
                exit_leg_id   VARCHAR,
                exit_leg_seq  INTEGER,
                exit_reason_code VARCHAR,
                is_partial_exit BOOLEAN DEFAULT FALSE,
                remaining_qty_after INTEGER,
                created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS broker_order_lifecycle_trace_exp (
                -- Broker 生命周期真相源：回答“何时接受、何时拒绝、何时成交、何时过期”。
                run_id       VARCHAR NOT NULL,
                order_id     VARCHAR NOT NULL,
                event_stage  VARCHAR NOT NULL,
                signal_id    VARCHAR,
                trade_id     VARCHAR,
                code         VARCHAR NOT NULL,
                action       VARCHAR NOT NULL,
                pattern      VARCHAR NOT NULL,
                event_date   DATE    NOT NULL,
                execute_date DATE,
                order_status VARCHAR,
                reason_code  VARCHAR,
                origin       VARCHAR NOT NULL,
                quantity     INTEGER,
                price        DOUBLE,
                is_paper     BOOLEAN DEFAULT FALSE,
                position_id  VARCHAR,
                exit_plan_id VARCHAR,
                exit_leg_id  VARCHAR,
                exit_leg_seq INTEGER,
                exit_leg_count INTEGER,
                exit_reason_code VARCHAR,
                is_partial_exit BOOLEAN DEFAULT FALSE,
                remaining_qty_before INTEGER,
                remaining_qty_after INTEGER,
                created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (run_id, order_id, event_stage)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS l4_stock_trust (
                code                VARCHAR NOT NULL PRIMARY KEY,
                tier                VARCHAR DEFAULT 'ACTIVE',
                consecutive_losses  INTEGER DEFAULT 0,
                on_probation        BOOLEAN DEFAULT FALSE,
                last_demote_date    DATE,
                last_promote_date   DATE,
                updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS l4_daily_report (
                date                 DATE NOT NULL PRIMARY KEY,
                candidates_count     INTEGER,
                signals_count        INTEGER,
                trades_count         INTEGER,
                win_rate             DOUBLE,
                avg_win              DOUBLE,
                avg_loss             DOUBLE,
                profit_factor        DOUBLE,
                expected_value       DOUBLE,
                max_drawdown         DOUBLE,
                max_consecutive_loss INTEGER,
                skewness             DOUBLE,
                rolling_ev_30d       DOUBLE,
                sharpe_30d           DOUBLE,
                reject_rate          DOUBLE,
                missing_rate         DOUBLE,
                exposure_rate        DOUBLE,
                failure_reason_breakdown VARCHAR,
                opportunity_count    INTEGER,
                filled_count         INTEGER,
                skip_cash_count      INTEGER,
                skip_maxpos_count    INTEGER,
                participation_rate   DOUBLE
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS l4_pattern_stats (
                date           DATE NOT NULL,
                pattern        VARCHAR NOT NULL,
                trade_count    INTEGER,
                win_rate       DOUBLE,
                avg_win        DOUBLE,
                avg_loss       DOUBLE,
                profit_factor  DOUBLE,
                expected_value DOUBLE,
                PRIMARY KEY (date, pattern)
            )
            """,
            # Meta
            """
            CREATE TABLE IF NOT EXISTS _meta_fetch_progress (
                data_type    VARCHAR NOT NULL PRIMARY KEY,
                last_success DATE,
                last_attempt TIMESTAMP,
                status       VARCHAR DEFAULT 'OK',
                error_msg    VARCHAR
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS _meta_runs (
                run_id          VARCHAR NOT NULL PRIMARY KEY,
                start_time      TIMESTAMP,
                end_time        TIMESTAMP,
                modules         VARCHAR,
                status          VARCHAR,
                error_summary   VARCHAR,
                config_hash     VARCHAR,
                data_snapshot   VARCHAR,
                git_commit      VARCHAR,
                runtime_env     VARCHAR,
                mode            VARCHAR,
                variant         VARCHAR,
                artifact_root   VARCHAR,
                created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS _meta_schema_version (
                id             INTEGER PRIMARY KEY,
                schema_version INTEGER NOT NULL,
                updated_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
        ]

    def _ensure_schema_version(self, current_version: int) -> None:
        # v0.01 约束：版本不一致时阻断运行，避免“旧库+新代码”静默污染结果。
        row = self.conn.execute(
            "SELECT schema_version, updated_at FROM _meta_schema_version WHERE id = 1"
        ).fetchone()
        if row is None:
            self.conn.execute(
                """
                INSERT INTO _meta_schema_version(id, schema_version, updated_at)
                VALUES (1, ?, CURRENT_TIMESTAMP)
                """,
                [current_version],
            )
            return

        db_version = int(row[0])
        if db_version == current_version:
            return
        if db_version > current_version:
            raise RuntimeError(
                f"Schema version {db_version} is newer than code version {current_version}."
            )
        self._apply_schema_migrations(db_version, current_version)

    def get_schema_version(self) -> SchemaVersion:
        row = self.conn.execute(
            "SELECT schema_version, updated_at FROM _meta_schema_version WHERE id = 1"
        ).fetchone()
        if row is None:
            return SchemaVersion(schema_version=0, updated_at=None)
        return SchemaVersion(schema_version=int(row[0]), updated_at=row[1])

    def bulk_upsert(self, table: str, df: pd.DataFrame) -> int:
        if df.empty:
            return 0
        target_info = self.read_df(f"PRAGMA table_info('{table}')")
        if not target_info.empty:
            target_columns = target_info["name"].astype(str).tolist()
            normalized = df.copy()
            if (
                table == "l3_signal_rank_exp"
                and "bof_strength" in target_columns
                and "bof_strength" not in normalized.columns
                and "pattern_strength" in normalized.columns
            ):
                # 兼容旧库里仍要求 bof_strength NOT NULL 的历史 schema：
                # 当前主线正式口径已切到 pattern_strength，但回写旧库时保留镜像列，避免实验脚本在现网库上撞约束。
                normalized["bof_strength"] = normalized["pattern_strength"]
            normalized = normalized[[col for col in normalized.columns if col in target_columns]]
        else:
            normalized = df
        # 幂等核心：所有重跑覆盖写都走 upsert，禁止同主键重复追加。
        # 对 trace / sidecar 来说，这意味着“同一 run_id + 主键”永远只保留一份真相源记录。
        tmp_name = "_tmp_df_upsert"
        self.conn.register(tmp_name, normalized)
        try:
            columns = ", ".join(normalized.columns)
            self.conn.execute(f"INSERT OR REPLACE INTO {table} ({columns}) SELECT {columns} FROM {tmp_name}")
        finally:
            self.conn.unregister(tmp_name)
        return len(normalized)

    def bulk_insert(self, table: str, df: pd.DataFrame) -> int:
        if df.empty:
            return 0
        tmp_name = "_tmp_df_insert"
        self.conn.register(tmp_name, df)
        try:
            columns = ", ".join(df.columns)
            self.conn.execute(f"INSERT INTO {table} ({columns}) SELECT {columns} FROM {tmp_name}")
        finally:
            self.conn.unregister(tmp_name)
        return len(df)

    def read_df(self, sql: str, params: tuple[Any, ...] | list[Any] | None = None) -> pd.DataFrame:
        if params is None:
            return self.conn.execute(sql).df()
        return self.conn.execute(sql, params).df()

    def read_scalar(
        self, sql: str, params: tuple[Any, ...] | list[Any] | None = None
    ) -> Any | None:
        if params is None:
            row = self.conn.execute(sql).fetchone()
        else:
            row = self.conn.execute(sql, params).fetchone()
        if row is None:
            return None
        return row[0]

    def read_table(
        self,
        table: str,
        date_range: tuple[date, date] | None = None,
        codes: list[str] | None = None,
        date_col: str = "date",
        code_col: str = "code",
    ) -> pd.DataFrame:
        where_clauses: list[str] = []
        params: list[Any] = []

        if date_range is not None:
            where_clauses.append(f"{date_col} BETWEEN ? AND ?")
            params.extend([date_range[0], date_range[1]])
        if codes:
            placeholders = ", ".join(["?"] * len(codes))
            where_clauses.append(f"{code_col} IN ({placeholders})")
            params.extend(codes)

        sql = f"SELECT * FROM {table}"
        if where_clauses:
            sql += " WHERE " + " AND ".join(where_clauses)
        return self.read_df(sql, tuple(params))

    def read_table_asof(
        self,
        table: str,
        asof_date: date,
        codes: list[str] | None = None,
        date_col: str = "date",
        code_col: str = "code",
        extra_where: str | None = None,
        extra_params: tuple[Any, ...] | None = None,
    ) -> pd.DataFrame:
        # 防未来函数：统一由 Store 注入 date <= asof_date 约束。
        # 业务模块无需重复拼接“<= asof”条件，避免漏写。
        where_clauses = [f"{date_col} <= ?"]
        params: list[Any] = [asof_date]

        if codes:
            placeholders = ", ".join(["?"] * len(codes))
            where_clauses.append(f"{code_col} IN ({placeholders})")
            params.extend(codes)
        if extra_where:
            where_clauses.append(f"({extra_where})")
        if extra_params:
            params.extend(list(extra_params))

        sql = f"SELECT * FROM {table} WHERE " + " AND ".join(where_clauses)
        return self.read_df(sql, tuple(params))

    def get_selector_candidate_trace(self, run_id: str, signal_date: date, code: str) -> dict[str, Any] | None:
        row = self.read_df(
            """
            SELECT *
            FROM selector_candidate_trace_exp
            WHERE run_id = ? AND signal_date = ? AND code = ?
            LIMIT 1
            """,
            (run_id, signal_date, code),
        )
        if row.empty:
            return None
        record = dict(row.iloc[0].to_dict())
        selected_for_pas = record.get("selected_for_pas")
        legacy_selected_for_bof = record.get("selected_for_bof")
        if (
            ("selected_for_pas" not in record or pd.isna(selected_for_pas))
            and legacy_selected_for_bof is not None
            and not pd.isna(legacy_selected_for_bof)
        ):
            record["selected_for_pas"] = bool(legacy_selected_for_bof)
        return record

    def get_pas_trigger_trace(
        self,
        run_id: str,
        signal_date: date,
        code: str,
        detector: str,
    ) -> dict[str, Any] | None:
        row = self.read_df(
            """
            SELECT *
            FROM pas_trigger_trace_exp
            WHERE run_id = ? AND signal_date = ? AND code = ? AND detector = ?
            LIMIT 1
            """,
            (run_id, signal_date, code, detector),
        )
        if row.empty:
            return None
        record = dict(row.iloc[0].to_dict())
        for raw_key, parsed_key in (
            ("trace_payload_json", "trace_payload"),
            ("pattern_context_json", "pattern_context"),
        ):
            raw_value = record.get(raw_key)
            if not isinstance(raw_value, str) or not raw_value.strip():
                continue
            try:
                record[parsed_key] = json.loads(raw_value)
            except json.JSONDecodeError:
                continue
        return record

    def get_irs_industry_trace(self, run_id: str, signal_id: str) -> dict[str, Any] | None:
        row = self.read_df(
            """
            SELECT *
            FROM irs_industry_trace_exp
            WHERE run_id = ? AND signal_id = ? AND COALESCE(trace_scope, 'SIGNAL_ATTACH') = 'SIGNAL_ATTACH'
            LIMIT 1
            """,
            (run_id, signal_id),
        )
        if row.empty:
            return None
        return dict(row.iloc[0].to_dict())

    def get_mss_risk_overlay_trace(self, run_id: str, signal_id: str) -> dict[str, Any] | None:
        row = self.read_df(
            """
            SELECT *
            FROM mss_risk_overlay_trace_exp
            WHERE run_id = ? AND signal_id = ?
            LIMIT 1
            """,
            (run_id, signal_id),
        )
        if row.empty:
            return None
        return dict(row.iloc[0].to_dict())

    def get_broker_lifecycle_trace(self, run_id: str, order_id: str) -> pd.DataFrame:
        return self.read_df(
            """
            SELECT *
            FROM broker_order_lifecycle_trace_exp
            WHERE run_id = ? AND order_id = ?
            ORDER BY event_date ASC, event_stage ASC
            """,
            (run_id, order_id),
        )

    @staticmethod
    def _canonical_fetch_progress_key(data_type: str) -> str:
        # 外部合同已经统一成 `industry_member`，
        # 这里只保留旧进度键的内部兼容。
        mapping = {
            "sw_industry_member": "industry_member",
        }
        return mapping.get(data_type, data_type)

    def get_fetch_progress(self, data_type: str) -> date | None:
        data_type = self._canonical_fetch_progress_key(data_type)
        value = self.read_scalar(
            "SELECT last_success FROM _meta_fetch_progress WHERE data_type = ?", (data_type,)
        )
        return value

    def update_fetch_progress(
        self,
        data_type: str,
        last_date: date | None,
        status: str = "OK",
        error_msg: str | None = None,
    ) -> None:
        data_type = self._canonical_fetch_progress_key(data_type)
        payload = pd.DataFrame(
            [
                {
                    "data_type": data_type,
                    "last_success": last_date,
                    "last_attempt": datetime.utcnow(),
                    "status": status,
                    "error_msg": error_msg,
                }
            ]
        )
        self.bulk_upsert("_meta_fetch_progress", payload)

    def get_max_date(self, table: str, date_col: str = "date") -> date | None:
        return self.read_scalar(f"SELECT MAX({date_col}) FROM {table}")

    def next_trade_date(self, base_date: date) -> date | None:
        # 交易日历是一等公民：所有 T+1 推进必须走此函数，不用自然日+1。
        return self.read_scalar(
            """
            SELECT date FROM l1_trade_calendar
            WHERE is_trade_day = TRUE AND date > ?
            ORDER BY date
            LIMIT 1
            """,
            (base_date,),
        )

    def prev_trade_date(self, base_date: date) -> date | None:
        return self.read_scalar(
            """
            SELECT date FROM l1_trade_calendar
            WHERE is_trade_day = TRUE AND date < ?
            ORDER BY date DESC
            LIMIT 1
            """,
            (base_date,),
        )

    def close(self) -> None:
        self.conn.close()
