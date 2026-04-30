"""Shared interfaces for all regime-signal modules (M1–M5)."""

from __future__ import annotations

import abc
from typing import Any, ClassVar

import pandas as pd
from pydantic import BaseModel, Field


class SignalOutput(BaseModel):
    """Output contract every regime-signal module must return."""

    model_config = {"arbitrary_types_allowed": True}

    module_id: str = Field(description="Identifier of the producing module (e.g. 'm1_vol_regime')")
    asof: pd.Timestamp = Field(description="Point-in-time cutoff — no data after this date was used")
    value: float = Field(description="Primary signal value; semantics are module-specific")
    confidence: float = Field(ge=0.0, le=1.0, description="Estimated reliability in [0, 1]")
    drivers: dict[str, float] = Field(
        default_factory=dict,
        description="Named feature contributions that explain the signal value",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Module-specific diagnostics (regime labels, model params, etc.)",
    )


class RegimeModule(abc.ABC):
    """Abstract base class for M1–M5.

    Subclasses must declare a class-level ``module_id`` and implement
    ``compute_signal``.  The only hard rule: implementations must not
    access any row with index > asof (no look-ahead bias).
    """

    module_id: ClassVar[str]

    @abc.abstractmethod
    def compute_signal(
        self,
        data: pd.DataFrame,
        asof: pd.Timestamp,
    ) -> SignalOutput:
        """Compute the regime signal as of ``asof``.

        Parameters
        ----------
        data:
            Historical feature DataFrame indexed by date.  All columns
            required by the implementing module must be present.
        asof:
            Point-in-time cutoff.  Only rows with ``index <= asof`` may
            be read.

        Returns
        -------
        SignalOutput
            Signal value, confidence, named drivers, and diagnostic metadata.
        """
