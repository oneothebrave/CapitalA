"""Provider interfaces and implementations for data ingestion."""

from app.data_ingestion.providers.base import IngestionProvider, ProviderFetchResult

__all__ = ["IngestionProvider", "ProviderFetchResult"]
