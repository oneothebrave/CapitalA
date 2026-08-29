"""Filesystem storage helpers for raw ingestion payloads and manifests."""

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.core.config import settings
from app.data_ingestion.manifest import (
    IngestionRunManifest,
    RawArtifact,
    SourceType,
    utc_now,
)


class RawStorage:
    """Save immutable raw payloads under the configured data/raw directory."""

    def __init__(self, root: Path | str | None = None) -> None:
        self.root = Path(root) if root is not None else settings.data_dir / "raw"

    def save_raw_payload(
        self,
        *,
        source_type: SourceType,
        source_name: str,
        provider_dataset: str,
        payload: bytes | str | dict[str, Any] | list[Any],
        media_type: str = "application/json",
        ticker: str | None = None,
        cik: str | None = None,
        accession_number: str | None = None,
        source_url: str | None = None,
        available_at: datetime | None = None,
        metadata: dict[str, Any] | None = None,
        file_extension: str | None = None,
    ) -> RawArtifact:
        """Persist a raw payload and return the corresponding artifact record."""

        content = self._serialize_payload(payload, media_type)
        payload_hash = hashlib.sha256(content).hexdigest()
        ingested_at = utc_now()
        effective_available_at = available_at or ingested_at

        suffix = file_extension or self._extension_for_media_type(media_type)
        file_name = f"{ingested_at.strftime('%Y%m%dT%H%M%SZ')}-{uuid4().hex}{suffix}"

        path_parts = [source_type, provider_dataset]
        if ticker:
            path_parts.append(ticker.upper())
        elif cik:
            path_parts.append(f"CIK{cik.zfill(10)}")

        storage_dir = self.root.joinpath(*path_parts)
        storage_dir.mkdir(parents=True, exist_ok=True)
        raw_storage_path = storage_dir / file_name
        raw_storage_path.write_bytes(content)

        return RawArtifact(
            source_type=source_type,
            source_name=source_name,
            provider_dataset=provider_dataset,
            ticker=ticker.upper() if ticker else None,
            cik=cik,
            accession_number=accession_number,
            raw_storage_path=str(raw_storage_path),
            media_type=media_type,
            payload_hash=payload_hash,
            byte_size=len(content),
            source_url=source_url,
            ingested_at=ingested_at,
            available_at=effective_available_at,
            metadata=metadata or {},
        )

    @staticmethod
    def _serialize_payload(
        payload: bytes | str | dict[str, Any] | list[Any],
        media_type: str,
    ) -> bytes:
        if isinstance(payload, bytes):
            return payload
        if isinstance(payload, str):
            return payload.encode("utf-8")
        if media_type == "application/json":
            return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8")
        return str(payload).encode("utf-8")

    @staticmethod
    def _extension_for_media_type(media_type: str) -> str:
        return {
            "application/json": ".json",
            "text/html": ".html",
            "text/csv": ".csv",
            "text/plain": ".txt",
            "application/xml": ".xml",
            "application/pdf": ".pdf",
        }.get(media_type, ".bin")


def write_manifest(
    manifest: IngestionRunManifest,
    *,
    root: Path | str | None = None,
) -> Path:
    """Write an ingestion manifest JSON file and return its path."""

    manifest_root = (
        Path(root) if root is not None else settings.data_dir / "manifests" / "ingestion_runs"
    )
    manifest_dir = manifest_root / manifest.job_name
    manifest_dir.mkdir(parents=True, exist_ok=True)
    path = manifest_dir / f"{manifest.run_id}.json"
    path.write_text(manifest.model_dump_json(indent=2), encoding="utf-8")
    return path
