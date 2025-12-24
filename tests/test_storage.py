from datetime import date

from src.core.storage.local_storage import LocalStorage
from src.core.storage.run_index import RunIndex
from src.core.storage.training_writer import TrainingArtifactWriter
from src.tools import placeholder_tools


def test_local_storage_round_trip(tmp_path):
    storage = LocalStorage(str(tmp_path))
    storage.ensure_dir("run-1")

    payload = {"value": 42}
    json_path = storage.write_json("run-1/data.json", payload)
    text_path = storage.write_text("run-1/notes.txt", "hello")

    assert storage.read_json("run-1/data.json") == payload
    assert tmp_path.joinpath("run-1", "notes.txt").read_text(encoding="utf-8") == "hello"
    assert storage.exists("run-1/data.json")
    assert storage.path("run-1/notes.txt") == text_path
    assert "run-1" in storage.list_runs()
    assert json_path.endswith("data.json")


def test_training_artifact_writer(tmp_path):
    storage = LocalStorage(str(tmp_path))
    writer = TrainingArtifactWriter(storage)

    output = writer.write(
        "training/run-123",
        {"analysis_packet": {"a": 1}, "draft_report": "draft"},
    )

    assert tmp_path.joinpath("training", "run-123", "analysis_packet.json").exists()
    assert tmp_path.joinpath("training", "run-123", "draft_report.txt").exists()
    assert output["analysis_packet"].endswith("analysis_packet.json")
    assert output["draft_report"].endswith("draft_report.txt")


def test_run_index_tracks_runs(tmp_path):
    run_index = RunIndex(str(tmp_path / "run_index.json"))

    run_index.put(
        "ACME",
        "2024-01-01",
        "run-1",
        {
            "run_id": "run-1",
            "status": "approved",
            "created_at": "2024-01-01T00:00:00",
        },
    )
    run_index.put(
        "ACME",
        "2024-01-02",
        "run-2",
        {
            "run_id": "run-2",
            "status": "approved",
            "created_at": "2024-02-01T00:00:00",
        },
    )

    latest = run_index.latest_approved("ACME")
    assert latest is not None
    assert latest["run_id"] == "run-2"
    assert run_index.find_by_run_id("run-1")["status"] == "approved"


def test_init_run_context_creates_directories(tmp_path):
    storage = LocalStorage(str(tmp_path))

    context = placeholder_tools.init_run_context(
        ticker="ACME",
        as_of_date=date(2024, 1, 1),
        mode="test",
        model_id="public:gpt-x",
        storage=storage,
    )

    assert context.run_id
    assert tmp_path.joinpath(context.paths.raw_path).exists()
    assert tmp_path.joinpath(context.paths.parsed_path).exists()
    assert tmp_path.joinpath(context.paths.report_path).exists()
    assert tmp_path.joinpath(context.paths.trace_path).exists()
