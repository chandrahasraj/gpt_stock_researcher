from datetime import date

from src.core.config import get_settings
from src.core.storage.run_index import RunIndex
from src.pipelines.stock_pipeline import run_pipeline


def test_run_pipeline_writes_outputs(tmp_path, monkeypatch):
    monkeypatch.setenv("STOCK_RUNS_DIR", str(tmp_path))
    get_settings.cache_clear()

    result = run_pipeline(
        ticker="ACME",
        as_of_date=date(2024, 1, 1),
        mode="test",
        model_id="public:gpt-x",
        refresh=False,
        max_iters=1,
    )

    assert result["status"] == "blocked"
    assert tmp_path.joinpath(result["report_path"]).exists()
    assert tmp_path.joinpath(result["analysis_packet_path"]).exists()
    assert tmp_path.joinpath(result["citations_map_path"]).exists()

    run_index = RunIndex(str(tmp_path / "run_index.json"))
    saved = run_index.find_by_run_id(result["run_id"])
    assert saved is not None
    assert saved["status"] == "blocked"
