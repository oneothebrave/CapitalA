"""Base provider protocol for external data retrieval."""

from __future__ import annotations

from typing import Any, Protocol

from pydantic import BaseModel, Field

from app.data_ingestion.manifest import IngestionRequest


class ProviderFetchResult(BaseModel):
    """Raw provider response before it is normalized or interpreted."""

    payload: bytes | str | dict[str, Any] | list[Any]
    media_type: str = "application/json"
    source_url: str | None = None
    provider_record_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class IngestionProvider(Protocol):
    """Contract implemented by SEC, market data, news, and IR providers."""

    source_name: str

    def fetch(self, request: IngestionRequest) -> ProviderFetchResult:
        """Retrieve raw data for an ingestion request."""

        ...
