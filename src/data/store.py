from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

import duckdb
import pandas as pd

CURRENT_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class SchemaVersion:
    schema_version: int
    updated_at: datetime | None


class Store:
    """DuckDB unified storage gateway."""

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
            CREATE TABLE IF NOT EXISTS l1_sw_industry_member (
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
                date               DATE NOT NULL PRIMARY KEY,
                score              DOUBLE,
                signal             VARCHAR,
                -- Phase 0-2 正式消费面仍只有 score/signal + 六因子展开。
                -- phase / phase_trend / phase_days / position_advice / risk_regime
                -- 属于 Phase 3 正文，不应在这一阶段静默塞进 formal schema。
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
                volatility         DOUBLE
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
                base_max_positions             INTEGER NOT NULL,
                base_risk_per_trade_pct        DOUBLE NOT NULL,
                base_max_position_pct          DOUBLE NOT NULL,
                max_positions_mult             DOUBLE NOT NULL,
                risk_per_trade_mult            DOUBLE NOT NULL,
                max_position_mult              DOUBLE NOT NULL,
                effective_max_positions        INTEGER NOT NULL,
                effective_risk_per_trade_pct   DOUBLE NOT NULL,
                effective_max_position_pct     DOUBLE NOT NULL,
                holdings_before                INTEGER NOT NULL,
                available_cash                 DOUBLE NOT NULL,
                portfolio_market_value         DOUBLE NOT NULL,
                decision_status                VARCHAR NOT NULL,
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
                PRIMARY KEY (code, calc_date)
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
        raise RuntimeError(
            "Schema migration required. Rebuild DB or provide migration script "
            f"(db={db_version}, code={current_version})."
        )

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
        # 注意：这里会把结果完整物化成 pandas DataFrame。
        # 主链高频路径应尽量只在“窗口已受控”的查询上使用它；更大的 join / group / rank
        # 优先留在 DuckDB 里完成，再把缩小后的结果取回 Python。
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

    def get_fetch_progress(self, data_type: str) -> date | None:
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
