import hashlib
import json
from pathlib import Path

from app.data_ingestion.manifest import IngestionRequest, IngestionRunManifest
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
