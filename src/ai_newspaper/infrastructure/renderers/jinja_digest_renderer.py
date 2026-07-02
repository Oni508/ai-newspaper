from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from ai_newspaper.domain.models import AnalysisResult, Article, Category, Digest


@dataclass(frozen=True)
class RenderedArticle:
    title: str
    url: str
    source_name: str
    category: Category
    category_label: str
    published_at: datetime | None
    source_summary: str
    analysis_summary: tuple[str, ...]
    background: tuple[str, ...]
    business_explainer: tuple[str, ...]
    conditional_scenarios: tuple[str, ...]
    uncertainty: tuple[str, ...]
    next_checks: tuple[str, ...]


@dataclass(frozen=True)
class DigestSection:
    title: str
    articles: tuple[RenderedArticle, ...]


@dataclass(frozen=True)
class DigestView:
    generated_at: datetime
    label: str
    top_items: tuple[RenderedArticle, ...]
    sections: tuple[DigestSection, ...]
    business_items: tuple[RenderedArticle, ...]
    watch_items: tuple[RenderedArticle, ...]
    references: tuple[RenderedArticle, ...]


class JinjaDigestRenderer:
    def __init__(
        self,
        template_dir: Path,
        template_name: str = "digest.html.j2",
    ) -> None:
        self._environment = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(["html", "xml", "j2"]),
        )
        self._template_name = template_name

    def render(self, digest: Digest) -> str:
        template = self._environment.get_template(self._template_name)
        return template.render(digest=digest, view=_build_view(digest))


def _build_view(digest: Digest) -> DigestView:
    analyses_by_url = {analysis.article_url: analysis for analysis in digest.analyses}
    articles = tuple(
        _rendered_article(article, analyses_by_url.get(article.url))
        for article in digest.articles
    )
    sections = tuple(
        DigestSection(
            title=title,
            articles=tuple(
                article
                for article in articles
                if article.category == category
            ),
        )
        for category, title in _CATEGORY_SECTIONS
    )

    return DigestView(
        generated_at=digest.edition.generated_at,
        label=digest.edition.label,
        top_items=articles[:5],
        sections=sections,
        business_items=tuple(
            article for article in articles if article.business_explainer
        ),
        watch_items=tuple(
            article
            for article in articles
            if article.conditional_scenarios or article.next_checks
        ),
        references=articles,
    )


def _rendered_article(
    article: Article,
    analysis: AnalysisResult | None,
) -> RenderedArticle:
    return RenderedArticle(
        title=article.title,
        url=article.url,
        source_name=article.source_name,
        category=article.category,
        category_label=_category_label(article.category),
        published_at=article.published_at,
        source_summary=article.summary,
        analysis_summary=_split_paragraphs(analysis.summary if analysis else ""),
        background=_split_paragraphs(analysis.background if analysis else ""),
        business_explainer=_split_paragraphs(
            analysis.business_explainer if analysis else ""
        ),
        conditional_scenarios=(
            analysis.conditional_scenarios if analysis else ()
        ),
        uncertainty=_split_paragraphs(analysis.uncertainty if analysis else ""),
        next_checks=analysis.next_checks if analysis else (),
    )


def _split_paragraphs(text: str) -> tuple[str, ...]:
    return tuple(line.strip() for line in text.splitlines() if line.strip())


def _category_label(category: Category) -> str:
    labels = {
        Category.POLITICS_ECONOMY: "政治・経済",
        Category.BUSINESS_TECHNOLOGY: "企業・技術",
        Category.INTERNATIONAL: "国際",
    }
    return labels[category]


_CATEGORY_SECTIONS = (
    (Category.POLITICS_ECONOMY, "政治・経済"),
    (Category.BUSINESS_TECHNOLOGY, "企業・技術"),
    (Category.INTERNATIONAL, "国際"),
)
