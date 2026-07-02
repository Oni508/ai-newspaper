from __future__ import annotations

from ai_newspaper.domain.models import AnalysisResult, Article, Category


class DummyNewsAnalyzer:
    """Deterministic offline analyzer for development and tests."""

    def analyze(self, articles: list[Article]) -> list[AnalysisResult]:
        return [self._analyze_article(article) for article in articles]

    def _analyze_article(self, article: Article) -> AnalysisResult:
        title = _clean_text(article.title, fallback="Untitled article")
        source = _clean_text(article.source_name, fallback="unknown source")
        article_summary = _clean_text(
            article.summary,
            fallback="source summary unavailable",
        )
        category_label = _category_label(article.category)

        return AnalysisResult(
            article_url=article.url,
            summary=(
                f"見出し: {title}\n"
                f"何が起きたか: {source} が {category_label} 分野のニュースとして"
                f"「{title}」を報じています。記事要約: {article_summary}"
            ),
            background=(
                "なぜ重要か: この話題は政策、企業戦略、技術動向、国際関係のいずれかに"
                "影響する可能性があるため、単発の出来事ではなく周辺文脈とあわせて"
                "確認する価値があります。\n"
                "専門家視点: 発表内容そのものに加えて、関係者の利害、規制環境、"
                "競争条件、実行時期を分けて読む必要があります。"
            ),
            business_explainer=_business_explainer(article),
            conditional_scenarios=(
                "今後の注視点: 追加発表、公式資料、規制当局や取引先の反応、"
                "競合の対応が出るかを確認します。",
                "条件付きシナリオ: もし関連する政策や企業施策が継続するなら、"
                "中期的な競争環境や利用者行動に影響する可能性があります。",
                "条件付きシナリオ: もし続報が限定的なら、短期的な話題にとどまる"
                "可能性もあります。",
            ),
            uncertainty=(
                "不確実性: Dummy Analyzer は記事本文を深く読まず、入力された"
                "メタデータだけで定型分析を生成します。事実関係、影響範囲、時期は"
                "一次情報と複数媒体で確認が必要です。株価や売買タイミングは予測しません。"
            ),
            next_checks=(
                "元記事と公式発表を確認する。",
                "関連する政策、製品、企業戦略、国際関係の続報を確認する。",
                "収益、利益率、競争、規制、ブランド、供給網への関係は断定せずに確認する。",
            ),
        )


def _clean_text(value: str, *, fallback: str) -> str:
    text = " ".join(value.split())
    return text if text else fallback


def _category_label(category: Category) -> str:
    labels = {
        Category.POLITICS_ECONOMY: "政治・経済",
        Category.BUSINESS_TECHNOLOGY: "ビジネス・テクノロジー",
        Category.INTERNATIONAL: "国際情勢",
    }
    return labels[category]


def _business_explainer(article: Article) -> str:
    if article.category == Category.BUSINESS_TECHNOLOGY:
        return (
            "企業理解補助: このニュースでは、対象企業や製品がなぜ注目されているか、"
            "どの事業・技術・供給網に関係するかを確認します。収益、利益率、競争、"
            "規制、ブランドへの影響は短期要因と中長期要因を分けて見る必要があります。"
            "初心者は公式発表、製品概要、競合状況、規制や供給制約を次に確認するとよいです。"
            "これは買い・売り・保有の判断ではありません。"
        )
    return (
        "企業理解補助: 企業が関係する場合は、収益、利益率、競争、規制、"
        "ブランド、供給網との関係を確認します。ただし、この分析は投資判断、"
        "株価予測、売買タイミングの提案を行いません。"
    )
