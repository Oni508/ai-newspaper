from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime

import pytest

from ai_newspaper.domain.models import (
    AnalysisResult,
    Article,
    Category,
    Digest,
    DigestEdition,
    Importance,
    Topic,
)


def test_article_keeps_existing_fields_and_is_immutable() -> None:
    article = Article(
        title="Central bank updates policy",
        url="https://example.com/policy",
        source_name="Example News",
        category=Category.POLITICS_ECONOMY,
        published_at=datetime(2026, 7, 1, 8, 0),
        summary="Policy summary",
    )

    assert article.title == "Central bank updates policy"
    assert article.url == "https://example.com/policy"
    assert article.source_name == "Example News"
    assert article.category == Category.POLITICS_ECONOMY
    assert article.summary == "Policy summary"

    with pytest.raises(FrozenInstanceError):
        article.title = "Changed"


def test_topic_requires_non_empty_name() -> None:
    topic = Topic(
        name="semiconductor export policy",
        category=Category.BUSINESS_TECHNOLOGY,
        importance=Importance.HIGH,
    )

    assert topic.name == "semiconductor export policy"
    assert topic.category == Category.BUSINESS_TECHNOLOGY
    assert topic.importance == Importance.HIGH

    with pytest.raises(ValueError, match="topic name"):
        Topic(name="   ", category=Category.BUSINESS_TECHNOLOGY)


def test_digest_groups_articles_and_analyses() -> None:
    generated_at = datetime(2026, 7, 1, 18, 0)
    article = Article(
        title="Company announces AI product",
        url="https://example.com/ai-product",
        source_name="Example News",
        category=Category.BUSINESS_TECHNOLOGY,
    )
    analysis = AnalysisResult(
        article_url=article.url,
        summary="The company announced a new AI product.",
        background="The product is part of a broader platform strategy.",
        business_explainer="Revenue impact remains uncertain.",
        conditional_scenarios=("If adoption grows, competition may increase.",),
        uncertainty="Pricing details are not public.",
        next_checks=("Check product availability.",),
    )

    digest = Digest(
        edition=DigestEdition(generated_at=generated_at, label="evening"),
        articles=(article,),
        analyses=(analysis,),
    )

    assert digest.edition.generated_at == generated_at
    assert digest.edition.label == "evening"
    assert digest.articles == (article,)
    assert digest.analyses == (analysis,)
