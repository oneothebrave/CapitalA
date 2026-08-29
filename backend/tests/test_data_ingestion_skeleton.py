import hashlib
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.data_ingestion.manifest import IngestionError, IngestionRequest, IngestionRunManifest
from app.data_ingestion.storage import RawStorage, write_manifest


def test_raw_storage_saves_json_payload_and_returns_artifact(tmp_path: Path) -> None:
    storage = RawStorage(root=tmp_path / "raw")

    artifact = storage.save_raw_payload(
        source_type="sec",
        source_name="sec_edgar",
        provider_dataset="submissions",
        payload={"ticker": "NVDA", "cik": "1045810"},
        ticker="nvda",
        cik="1045810",
    )

    raw_path = tmp_path / "raw" / "sec" / "submissions" / "NVDA"
    saved_files = list(raw_path.glob("*.json"))

    assert len(saved_files) == 1
    assert saved_files[0] == Path(artifact.raw_storage_path)
    assert artifact.ticker == "NVDA"
    assert artifact.byte_size == saved_files[0].stat().st_size
    assert artifact.payload_hash == hashlib.sha256(saved_files[0].read_bytes()).hexdigest()


def test_manifest_finish_and_write_manifest(tmp_path: Path) -> None:
    request = IngestionRequest(
        source_type="sec",
        source_name="sec_edgar",
        retrieval_method="api",
        ticker="NVDA",
        cik="1045810",
    )
    manifest = IngestionRunManifest(
        job_name="ingest_sec_submissions",
        source_type="sec",
        source_name="sec_edgar",
        request=request,
    )

    manifest.finish()
    manifest_path = write_manifest(manifest, root=tmp_path / "manifests")
    written = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert manifest.status == "success"
    assert manifest.finished_at is not None
    assert written["run_id"] == manifest.run_id
    assert written["request"]["ticker"] == "NVDA"


def test_manifest_filters_artifacts_by_data_cutoff(tmp_path: Path) -> None:
    storage = RawStorage(root=tmp_path / "raw")
    data_cutoff_at = datetime(2024, 5, 1, 21, 0, tzinfo=UTC)

    visible_artifact = storage.save_raw_payload(
        source_type="news",
        source_name="news_provider",
        provider_dataset="ticker_news",
        payload={"ticker": "NVDA", "headline": "visible article"},
        ticker="NVDA",
        available_at=data_cutoff_at,
    )
    future_artifact = storage.save_raw_payload(
        source_type="news",
        source_name="news_provider",
        provider_dataset="ticker_news",
        payload={"ticker": "NVDA", "headline": "future article"},
        ticker="NVDA",
        available_at=data_cutoff_at + timedelta(minutes=1),
    )
    manifest = IngestionRunManifest(
        job_name="ingest_ticker_news",
        source_type="news",
        source_name="news_provider",
        artifacts=[visible_artifact, future_artifact],
    )

    assert manifest.available_artifacts(data_cutoff_at) == [visible_artifact]


def test_manifest_rejects_naive_data_cutoff() -> None:
    manifest = IngestionRunManifest(
        job_name="ingest_ticker_news",
        source_type="news",
        source_name="news_provider",
    )

    with pytest.raises(ValueError, match="timezone-aware"):
        manifest.available_artifacts(datetime(2024, 5, 1, 21, 0))


def test_ingestion_request_rejects_naive_data_cutoff() -> None:
    with pytest.raises(ValidationError):
        IngestionRequest(
            source_type="news",
            source_name="news_provider",
            retrieval_method="api",
            data_cutoff_at=datetime(2024, 5, 1, 21, 0),
        )


def test_manifest_records_failure_details(tmp_path: Path) -> None:
    manifest = IngestionRunManifest(
        job_name="ingest_ticker_news",
        source_type="news",
        source_name="news_provider",
    )

    manifest.add_error(
        IngestionError(
            message="rate limit exceeded",
            error_type="rate_limit",
            retryable=True,
            details={"status_code": 429},
        )
    )
    manifest.finish()

    manifest_path = write_manifest(manifest, root=tmp_path / "manifests")
    written = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert manifest.status == "failed"
    assert written["errors"][0]["message"] == "rate limit exceeded"
    assert written["errors"][0]["retryable"] is True
    assert written["errors"][0]["details"]["status_code"] == 429
