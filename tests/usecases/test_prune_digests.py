from __future__ import annotations

from datetime import datetime
from pathlib import Path

from ai_newspaper.domain.models import Digest, DigestEdition
from ai_newspaper.usecases.prune_digests import PruneDigests


class FakeStore:
    def __init__(self) -> None:
        self.deleted_generated_at: list[datetime] = []

    def delete_html(self, generated_at: datetime) -> Path:
        self.deleted_generated_at.append(generated_at)
        return Path(f"data/digests/digest_{generated_at:%Y-%m-%d_%H%M}.html")


class FakeDigestRepository:
    def __init__(self, digests: list[Digest]) -> None:
        self._digests = digests
        self.deleted: list[tuple[datetime, str]] = []

    def list_digests(self) -> list[Digest]:
        return list(self._digests)

    def delete_digest(self, generated_at: datetime, label: str) -> None:
        self.deleted.append((generated_at, label))


class FakeClock:
    def now(self) -> datetime:
        return datetime(2026, 7, 2, 18, 0)


def test_prune_digests_deletes_html_and_metadata_older_than_48_hours() -> None:
    old_digest = _digest(datetime(2026, 6, 30, 17, 59), "old")
    boundary_digest = _digest(datetime(2026, 6, 30, 18, 0), "boundary")
    recent_digest = _digest(datetime(2026, 7, 1, 18, 0), "recent")
    store = FakeStore()
    digest_repository = FakeDigestRepository(
        [recent_digest, boundary_digest, old_digest]
    )

    deleted = PruneDigests(
        store=store,
        digest_repository=digest_repository,
        clock=FakeClock(),
    ).execute()

    assert deleted == [Path("data/digests/digest_2026-06-30_1759.html")]
    assert store.deleted_generated_at == [old_digest.edition.generated_at]
    assert digest_repository.deleted == [
        (old_digest.edition.generated_at, old_digest.edition.label)
    ]


def _digest(generated_at: datetime, label: str) -> Digest:
    return Digest(edition=DigestEdition(generated_at=generated_at, label=label))
