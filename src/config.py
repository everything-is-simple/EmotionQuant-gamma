from __future__ import annotations

from datetime import date
from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Data source (dual-channel first, legacy single token fallback)
    tushare_token: str = Field(default="", alias="TUSHARE_TOKEN")
    tushare_primary_token: str = Field(default="", alias="TUSHARE_PRIMARY_TOKEN")
    tushare_primary_http_url: str = Field(default="", alias="TUSHARE_PRIMARY_HTTP_URL")
    tushare_primary_sdk_provider: str = Field(default="", alias="TUSHARE_PRIMARY_SDK_PROVIDER")
    tushare_primary_rate_limit_per_min: int = Field(
        default=0, alias="TUSHARE_PRIMARY_RATE_LIMIT_PER_MIN"
    )
    tushare_fallback_token: str = Field(default="", alias="TUSHARE_FALLBACK_TOKEN")
    tushare_fallback_http_url: str = Field(default="", alias="TUSHARE_FALLBACK_HTTP_URL")
    tushare_fallback_sdk_provider: str = Field(default="", alias="TUSHARE_FALLBACK_SDK_PROVIDER")
    tushare_fallback_rate_limit_per_min: int = Field(
        default=0, alias="TUSHARE_FALLBACK_RATE_LIMIT_PER_MIN"
    )
    tushare_sdk_provider: str = Field(default="tushare", alias="TUSHARE_SDK_PROVIDER")
    tushare_http_url: str = Field(default="", alias="TUSHARE_HTTP_URL")
    tushare_rate_limit_per_min: int = Field(default=300, alias="TUSHARE_RATE_LIMIT_PER_MIN")
    akshare_enabled: bool = Field(default=True, alias="AKSHARE_ENABLED")

    # Paths
    data_path: str = Field(default="", alias="DATA_PATH")
    temp_path: str = Field(default="", alias="TEMP_PATH")
    log_path: str = Field(default="", alias="LOG_PATH")
    raw_db_path: str = Field(default="", alias="RAW_DB_PATH")

    # Repo metadata
    repo_remote_url: str = Field(
        default="https://github.com/everything-is-simple/EmotionQuant-gamma",
        alias="REPO_REMOTE_URL",
    )
    repo_backup_remote_url: str = Field(
        default="https://gitee.com/wangweiyun2233/EmotionQuant-gamma",
        alias="REPO_BACKUP_REMOTE_URL",
    )

    # Environment
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    environment: str = Field(default="development", alias="ENVIRONMENT")

    # Funnel switches
    enable_mss_gate: bool = Field(default=False, alias="ENABLE_MSS_GATE")
    enable_irs_filter: bool = Field(default=False, alias="ENABLE_IRS_FILTER")
    enable_gene_filter: bool = Field(default=False, alias="ENABLE_GENE_FILTER")
    enable_dtt_mode: bool = Field(default=True, alias="ENABLE_DTT_MODE")
    pipeline_mode: str = Field(default="", alias="PIPELINE_MODE")

    # Trading and backtest params
    backtest_initial_cash: float = Field(default=1_000_000, alias="BACKTEST_INITIAL_CASH")
    commission_rate: float = Field(default=0.0003, alias="COMMISSION_RATE")
    min_commission: float = Field(default=5.0, alias="MIN_COMMISSION")
    stamp_duty_rate: float = Field(default=0.001, alias="STAMP_DUTY_RATE")
    transfer_fee_rate: float = Field(default=0.00002, alias="TRANSFER_FEE_RATE")
    slippage_bps: float = Field(default=0.0, alias="SLIPPAGE_BPS")
    stop_loss_pct: float = Field(default=0.05, alias="STOP_LOSS_PCT")
    trailing_stop_pct: float = Field(default=0.08, alias="TRAILING_STOP_PCT")
    risk_per_trade_pct: float = Field(default=0.008, alias="RISK_PER_TRADE_PCT")
    max_position_pct: float = Field(default=0.10, alias="MAX_POSITION_PCT")
    max_positions: int = Field(default=10, alias="MAX_POSITIONS")
    risk_free_rate: float = Field(default=0.015, alias="RISK_FREE_RATE")

    # Build windows
    history_start: date = Field(default=date(2023, 1, 1), alias="HISTORY_START")

    # Selector/Strategy defaults (v0.01)
    candidate_top_n: int = Field(default=100, alias="CANDIDATE_TOP_N")
    # DTT 主线的初选分只用于算力调度；通过 mode 做消融，而不是把交易语义写回 Selector。
    preselect_score_mode: str = Field(
        default="amount_plus_volume_ratio",
        alias="PRESELECT_SCORE_MODE",
    )
    irs_top_n: int = Field(default=10, alias="IRS_TOP_N")
    irs_min_industries_per_day: int = Field(default=25, alias="IRS_MIN_INDUSTRIES_PER_DAY")
    mss_variant: str = Field(default="zscore_weighted6", alias="MSS_VARIANT")
    mss_gate_mode: str = Field(default="bearish_only", alias="MSS_GATE_MODE")
    mss_bullish_threshold: float = Field(default=65.0, alias="MSS_BULLISH_THRESHOLD")
    mss_bearish_threshold: float = Field(default=35.0, alias="MSS_BEARISH_THRESHOLD")
    mss_soft_gate_candidate_top_n: int = Field(default=30, alias="MSS_SOFT_GATE_CANDIDATE_TOP_N")
    # v0.01-plus 当前先只在 MSS 控仓位变体下启用市场级风控覆盖，其它链路维持原口径。
    mss_risk_overlay_variant: str = Field(
        default="v0_01_dtt_bof_plus_irs_mss_score",
        alias="MSS_RISK_OVERLAY_VARIANT",
    )
    mss_bullish_max_positions_mult: float = Field(
        default=1.0,
        alias="MSS_BULLISH_MAX_POSITIONS_MULT",
    )
    mss_neutral_max_positions_mult: float = Field(
        default=0.7,
        alias="MSS_NEUTRAL_MAX_POSITIONS_MULT",
    )
    mss_bearish_max_positions_mult: float = Field(
        default=0.4,
        alias="MSS_BEARISH_MAX_POSITIONS_MULT",
    )
    mss_bullish_risk_per_trade_mult: float = Field(
        default=1.0,
        alias="MSS_BULLISH_RISK_PER_TRADE_MULT",
    )
    mss_neutral_risk_per_trade_mult: float = Field(
        default=0.7,
        alias="MSS_NEUTRAL_RISK_PER_TRADE_MULT",
    )
    mss_bearish_risk_per_trade_mult: float = Field(
        default=0.4,
        alias="MSS_BEARISH_RISK_PER_TRADE_MULT",
    )
    mss_bullish_max_position_mult: float = Field(
        default=1.0,
        alias="MSS_BULLISH_MAX_POSITION_MULT",
    )
    mss_neutral_max_position_mult: float = Field(
        default=0.7,
        alias="MSS_NEUTRAL_MAX_POSITION_MULT",
    )
    mss_bearish_max_position_mult: float = Field(
        default=0.4,
        alias="MSS_BEARISH_MAX_POSITION_MULT",
    )
    min_list_days: int = Field(default=60, alias="MIN_LIST_DAYS")
    # TuShare amount 单位为千元；v0.01 基线默认流动性阈值为 5,000 万元 = 50,000（千元）。
    min_amount: float = Field(default=50_000, alias="MIN_AMOUNT")
    dtt_variant: str = Field(
        default="v0_01_dtt_bof_plus_irs_score",
        alias="DTT_VARIANT",
    )
    dtt_score_fill: float = Field(default=50.0, alias="DTT_SCORE_FILL")
    dtt_top_n: int = Field(default=50, alias="DTT_TOP_N")
    dtt_bof_weight: float = Field(default=0.50, alias="DTT_BOF_WEIGHT")
    dtt_irs_weight: float = Field(default=0.30, alias="DTT_IRS_WEIGHT")
    dtt_mss_weight: float = Field(default=0.20, alias="DTT_MSS_WEIGHT")

    # PAS parameters (v0.01 only BOF active)
    pas_patterns: str = Field(default="bof", alias="PAS_PATTERNS")
    pas_combination: str = Field(default="ANY", alias="PAS_COMBINATION")
    pas_lookback_days: int = Field(default=60, alias="PAS_LOOKBACK_DAYS")
    pas_min_history_days: int = Field(default=30, alias="PAS_MIN_HISTORY_DAYS")
    # BOF 长窗口回测按批拉历史，避免 5000+ 标的逐只查库把个人 PC 内存打满。
    pas_eval_batch_size: int = Field(default=32, alias="PAS_EVAL_BATCH_SIZE")
    pas_bof_break_pct: float = Field(default=0.01, alias="PAS_BOF_BREAK_PCT")
    pas_bof_volume_mult: float = Field(default=1.2, alias="PAS_BOF_VOLUME_MULT")

    # Order lifecycle
    max_pending_trade_days: int = Field(default=1, alias="MAX_PENDING_TRADE_DAYS")

    @property
    def resolved_data_path(self) -> Path:
        if self.data_path.strip():
            path = Path(self.data_path.strip()).expanduser().resolve()
        else:
            path = Path.home() / ".emotionquant" / "data"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def resolved_temp_path(self) -> Path:
        if self.temp_path.strip():
            path = Path(self.temp_path.strip()).expanduser().resolve()
        else:
            path = Path.home() / ".emotionquant" / "temp"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def resolved_log_path(self) -> Path:
        if self.log_path.strip():
            path = Path(self.log_path.strip()).expanduser().resolve()
        else:
            path = self.resolved_data_path / "logs"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def pipeline_mode_normalized(self) -> str:
        raw_mode = self.pipeline_mode.strip().lower()
        if raw_mode in {"legacy", "dtt"}:
            return raw_mode
        return "dtt" if self.enable_dtt_mode else "legacy"

    @property
    def use_dtt_pipeline(self) -> bool:
        return self.pipeline_mode_normalized == "dtt"

    @property
    def dtt_variant_normalized(self) -> str:
        return self.dtt_variant.strip().lower()

    @property
    def mss_risk_overlay_enabled(self) -> bool:
        return (
            self.use_dtt_pipeline
            and self.dtt_variant_normalized == self.mss_risk_overlay_variant.strip().lower()
        )

    @property
    def db_path(self) -> Path:
        # v0.01 唯一执行库：main.py fetch/build/run/backtest 默认都读写这里。
        return self.resolved_data_path / "emotionquant.duckdb"

    @property
    def duckdb_dir(self) -> str:
        # 兼容旧脚本的 raw DuckDB/辅助库目录，不代表运行时主库。
        path = self.resolved_data_path / "duckdb"
        path.mkdir(parents=True, exist_ok=True)
        return str(path)

    @property
    def parquet_path(self) -> str:
        # 兼容旧版冷备/离线交换路径；v0.01 主链路不再把 Parquet 作为在线主存储。
        path = self.resolved_data_path / "parquet"
        path.mkdir(parents=True, exist_ok=True)
        return str(path)

    @property
    def pas_pattern_list(self) -> list[str]:
        # 配置用逗号字符串，运行时统一解析为小写列表。
        return [part.strip().lower() for part in self.pas_patterns.split(",") if part.strip()]

    @classmethod
    def from_env(cls, env_file: str = ".env") -> Settings:
        return cls(_env_file=env_file, _env_file_encoding="utf-8")  # type: ignore[call-arg]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()

