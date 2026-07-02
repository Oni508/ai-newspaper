from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from ai_newspaper.domain.models import Category
from ai_newspaper.domain.policies import (
    DIGEST_RETENTION,
    ForecastPolicy,
    RetentionPolicy,
    is_supported_category,
)


def test_supported_categories_include_first_version_scope() -> None:
    assert is_supported_category(Category.POLITICS_ECONOMY)
    assert is_supported_category(Category.BUSINESS_TECHNOLOGY)
    assert is_supported_category(Category.INTERNATIONAL)


def test_forecast_policy_allows_conditional_supported_forecast() -> None:
    policy = ForecastPolicy()
    text = (
        "If technology announcements continue, companies may adjust "
        "corporate strategy."
    )

    assert policy.allows_forecast(Category.BUSINESS_TECHNOLOGY, text)


def test_forecast_policy_blocks_forbidden_topic() -> None:
    policy = ForecastPolicy()
    text = "If stock price movements continue, trading interest may increase."

    assert policy.is_forbidden_topic(text)
    assert not policy.allows_forecast(Category.BUSINESS_TECHNOLOGY, text)


def test_forecast_policy_blocks_investment_advice_terms() -> None:
    policy = ForecastPolicy()
    text = "If policy changes continue, this would be a buy recommendation."

    assert policy.contains_investment_advice(text)
    assert not policy.allows_forecast(Category.POLITICS_ECONOMY, text)


def test_forecast_policy_requires_conditional_scenario() -> None:
    policy = ForecastPolicy()
    text = "Technology announcements will reshape corporate strategy."

    assert policy.is_allowed_topic(text)
    assert not policy.is_conditional_scenario(text)
    assert not policy.allows_forecast(Category.BUSINESS_TECHNOLOGY, text)


def test_retention_policy_calculates_expiration_cutoff() -> None:
    now = datetime(2026, 7, 1, 18, 0)
    policy = RetentionPolicy()

    assert policy.retention == DIGEST_RETENTION
    assert policy.expires_before(now) == datetime(2026, 6, 29, 18, 0)


def test_retention_policy_requires_positive_duration() -> None:
    with pytest.raises(ValueError, match="retention"):
        RetentionPolicy(retention=timedelta(0))
