"""Pydantic models for ingestion run audit manifests."""

from datetime import UTC, datetime
from typing import Any, Literal, Self
from uuid import uuid4

from pydantic import AwareDatetime, BaseModel, Field

SourceType = Literal[
    "sec",
    "exchange_reference",
    "market_data",
    "corporate_actions",
    "news",
    "ir",
    "macro",
    "other",
]

RetrievalMethod = Literal["api", "bulk_file", "rss", "web_page", "manual"]

IngestionStatus = Literal["running", "success", "partial_success", "failed"]


def utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp."""

    return datetime.now(UTC)


def require_timezone_aware(value: datetime | None) -> datetime | None:
    """Reject naive datetimes so point-in-time comparisons are explicit."""

    if value is not None and value.utcoffset() is None:
        msg = "datetime fields must be timezone-aware"
        raise ValueError(msg)
    return value


class IngestionRequest(BaseModel):
    """Input and source metadata for one external retrieval request."""

    source_type: SourceType
    source_name: str
    retrieval_method: RetrievalMethod
    url: str | None = None
    provider: str | None = None
    provider_dataset: str | None = None
    provider_record_id: str | None = None
    ticker: str | None = None
    cik: str | None = None
    accession_number: str | None = None
    as_of_date: str | None = None
    data_cutoff_at: AwareDatetime | None = None
    request_params: dict[str, Any] = Field(default_factory=dict)
    requested_at: AwareDatetime = Field(default_factory=utc_now)


class RawArtifact(BaseModel):
    """A raw file or payload saved by an ingestion run."""

    artifact_id: str = Field(default_factory=lambda: str(uuid4()))
    source_type: SourceType
    source_name: str
    provider_dataset: str | None = None
    provider_record_id: str | None = None
    ticker: str | None = None
    cik: str | None = None
    accession_number: str | None = None
    raw_storage_path: str
    media_type: str
    payload_hash: str
    byte_size: int
    source_url: str | None = None
    source_published_at: AwareDatetime | None = None
    source_updated_at: AwareDatetime | None = None
    accepted_at: AwareDatetime | None = None
    ingested_at: AwareDatetime = Field(default_factory=utc_now)
    available_at: AwareDatetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class IngestionError(BaseModel):
    """Error details captured during a run without losing auditability."""

    message: str
    error_type: str | None = None
    retryable: bool = False
    details: dict[str, Any] = Field(default_factory=dict)
    occurred_at: AwareDatetime = Field(default_factory=utc_now)


class IngestionRunManifest(BaseModel):
    """Audit record for one ingestion job execution."""

    run_id: str = Field(default_factory=lambda: str(uuid4()))
    job_name: str
    job_version: str = "v1"
    source_type: SourceType
    source_name: str
    status: IngestionStatus = "running"
    started_at: AwareDatetime = Field(default_factory=utc_now)
    finished_at: AwareDatetime | None = None
    request: IngestionRequest | None = None
    artifacts: list[RawArtifact] = Field(default_factory=list)
    errors: list[IngestionError] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def add_artifact(self, artifact: RawArtifact) -> None:
        self.artifacts.append(artifact)

    def add_error(self, error: IngestionError) -> None:
        self.errors.append(error)

    def finish(self, status: IngestionStatus | None = None) -> Self:
        if status is not None:
            self.status = status
        elif self.errors and self.artifacts:
            self.status = "partial_success"
        elif self.errors:
            self.status = "failed"
        else:
            self.status = "success"

        self.finished_at = utc_now()
        return self

    def available_artifacts(self, data_cutoff_at: datetime) -> list[RawArtifact]:
        """Return only artifacts available at or before the supplied cutoff."""

        require_timezone_aware(data_cutoff_at)
        return [
            artifact
            for artifact in self.artifacts
            if artifact.available_at <= data_cutoff_at
        ]
