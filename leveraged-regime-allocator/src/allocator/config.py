"""Central configuration via Pydantic Settings — no hardcoded magic numbers anywhere else."""

from __future__ import annotations

from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DataSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="DATA_", env_file=".env", extra="ignore")

    fred_api_key: str = Field(default="", description="FRED API key (fred.stlouisfed.org)")
    tiingo_api_key: str = Field(default="", description="Tiingo API key")
    cache_dir: Path = Field(default=Path("data/cache"))
    raw_dir: Path = Field(default=Path("data/raw"))
    processed_dir: Path = Field(default=Path("data/processed"))


class BacktestSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="BACKTEST_", env_file=".env", extra="ignore")

    start_date: str = Field(default="1990-01-01", description="In-sample start date (YYYY-MM-DD)")
    # OOS period is TABU until final evaluation — never train on dates >= oos_start
    oos_start_date: str = Field(default="2015-01-01", description="Out-of-sample start (DO NOT touch)")
    sma_period: int = Field(default=200, ge=1, description="Baseline SMA lookback in trading days")
    min_history_days: int = Field(default=504, ge=1, description="Minimum trading days required before first signal")


class PortfolioSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="PORTFOLIO_", env_file=".env", extra="ignore")

    initial_capital: float = Field(default=10_000.0, gt=0)
    min_leverage: float = Field(default=0.0, ge=0.0, description="Floor: fully in cash")
    max_leverage: float = Field(default=3.0, le=3.0, description="Ceiling: 3x S&P 500 exposure")
    rebalance_threshold: float = Field(
        default=0.05,
        gt=0,
        description="Only rebalance when target deviates by more than this fraction",
    )

    @field_validator("max_leverage")
    @classmethod
    def max_leverage_exceeds_min(cls, v: float, info: object) -> float:  # noqa: ANN001
        return v


class TaxSettings(BaseSettings):
    """German retail investor tax model (Abgeltungsteuer + Solidaritätszuschlag)."""

    model_config = SettingsConfigDict(env_prefix="TAX_", env_file=".env", extra="ignore")

    kapitalertragsteuer_rate: float = Field(default=0.25, description="KESt: 25%")
    solidaritaetszuschlag_rate: float = Field(default=0.055, description="SolZ: 5.5% of KESt")
    trade_cost_eur: float = Field(default=1.0, ge=0.0, description="Fixed cost per trade (Scalable/TR)")

    @property
    def effective_tax_rate(self) -> float:
        """Combined KESt + SolZ effective rate (≈ 26.375%)."""
        return self.kapitalertragsteuer_rate * (1 + self.solidaritaetszuschlag_rate)


class LiveSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="LIVE_", env_file=".env", extra="ignore")

    telegram_bot_token: str = Field(default="", description="Telegram bot token for alerts")
    telegram_chat_id: str = Field(default="", description="Telegram chat or channel ID")
    signal_hour_utc: int = Field(default=18, ge=0, le=23, description="Hour (UTC) to emit daily signal")


class Settings(BaseSettings):
    """Aggregate settings — instantiate once and pass around."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    data: DataSettings = Field(default_factory=DataSettings)
    backtest: BacktestSettings = Field(default_factory=BacktestSettings)
    portfolio: PortfolioSettings = Field(default_factory=PortfolioSettings)
    tax: TaxSettings = Field(default_factory=TaxSettings)
    live: LiveSettings = Field(default_factory=LiveSettings)


# Module-level singleton — import this everywhere instead of re-instantiating.
settings = Settings()
