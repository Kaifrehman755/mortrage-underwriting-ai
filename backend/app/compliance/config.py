"""Versioned compliance rule configuration.

Playbook rule: numeric thresholds and deadlines must come from a versioned
configuration copied from retrieved source text. This module intentionally ships
the production configuration with ``verified: false`` and no usable numeric
values. A deployment must replace a placeholder with a reviewed, sourced value
before the corresponding rule can return anything other than ``cannot_verify``.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

_DEFAULT_CONFIG_PATH = Path(__file__).with_name("rules.v1.json")


class RuleSettings(BaseModel):
    """Thresholds and provenance for one rule."""

    model_config = ConfigDict(extra="forbid")

    verified: bool = False
    source_ref: str = "TODO-VERIFY"
    values: dict[str, Any] = Field(default_factory=dict)


class ComplianceConfig(BaseModel):
    """Immutable-in-practice rule pack configuration."""

    model_config = ConfigDict(extra="forbid")

    rule_set_version: str = Field(..., min_length=1)
    rules: dict[str, RuleSettings] = Field(default_factory=dict)

    @classmethod
    def load(cls, path: Path | None = None) -> ComplianceConfig:
        """Load a rule pack from JSON. Missing files fail closed."""
        config_path = path or _DEFAULT_CONFIG_PATH
        with config_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        return cls.model_validate(payload)

    def for_rule(self, rule_id: str) -> RuleSettings:
        """Return the rule's settings.

        A missing entry is treated as unverified. This is deliberate: a rule that
        is added to the registry without a reviewed config entry must abstain.
        """
        return self.rules.get(rule_id, RuleSettings())
