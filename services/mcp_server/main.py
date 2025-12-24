from __future__ import annotations

import logging
import uuid
from datetime import date
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pydantic import Field, field_validator

from src.core.config import get_settings
from src.core.logging import configure_logging
from services.mcp_server.model_registry import ModelRegistry
from services.mcp_server.model_router import ModelRouter
from services.mcp_server.tool_registry import ToolRegistry
from src.core.storage.local_storage import LocalStorage
from src.core.storage.run_index import RunIndex
from src.pipelines.stock_pipeline import run_pipeline

app = FastAPI(title="MCP Server")

settings = get_settings()
configure_logging(settings.log_level)
logger = logging.getLogger(__name__)

registry = ModelRegistry(Path(settings.model_registry_path))
router = ModelRouter()
tool_registry = ToolRegistry()
run_index = RunIndex(str(Path(settings.runs_dir) / "run_index.json"))
storage = LocalStorage(settings.runs_dir)


class RunRequest(BaseModel):
    ticker: str
    as_of_date: Optional[date] = None
    mode: str = "interactive"
    model_id: str = Field(default_factory=lambda: settings.default_model_id)
    refresh: bool = False
    thresholds: Dict[str, Any] = Field(default_factory=dict)
    max_iters: int = Field(default=1, ge=1)

    @field_validator("ticker")
    @classmethod
    def normalize_ticker(cls, value: str) -> str:
        normalized = value.strip().upper()
        if not normalized:
            raise ValueError("ticker is required")
        return normalized


class QueryRequest(BaseModel):
    ticker: str
    as_of_date: Optional[date] = None
    query_text: str
    refresh: bool = False
    model_id: Optional[str] = None

    @field_validator("ticker")
    @classmethod
    def normalize_ticker(cls, value: str) -> str:
        normalized = value.strip().upper()
        if not normalized:
            raise ValueError("ticker is required")
        return normalized

    @field_validator("query_text")
    @classmethod
    def validate_query_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("query_text is required")
        return value


class ModelGenerateRequest(BaseModel):
    model_id: str
    messages: list[Dict[str, Any]]
    tools_enabled: bool = False
    tool_schema: Dict[str, Any] = Field(default_factory=dict)
    context_refs: list[str] = Field(default_factory=list)
    run_id: str
    temperature: float = Field(default=0.2, ge=0.0, le=2.0)


@app.post("/v1/run")
def run_pipeline_endpoint(payload: RunRequest) -> Dict[str, Any]:
    run_id = uuid.uuid4().hex
    try:
        result = run_pipeline(
            ticker=payload.ticker,
            as_of_date=payload.as_of_date or date.today(),
            mode=payload.mode,
            model_id=payload.model_id,
            refresh=payload.refresh,
            thresholds=payload.thresholds,
            max_iters=payload.max_iters,
        )
    except Exception as exc:
        logger.exception("Pipeline run failed for %s", payload.ticker)
        raise HTTPException(status_code=500, detail="Pipeline execution failed") from exc
    return {"job_id": run_id, "run_id": result["run_id"], "status": result["status"]}


@app.get("/v1/run/{run_id}")
def get_run_status(run_id: str) -> Dict[str, Any]:
    entry = run_index.find_by_run_id(run_id)
    if entry:
        return entry
    raise HTTPException(status_code=404, detail="Run not found")


@app.post("/v1/query")
def query(payload: QueryRequest) -> Dict[str, Any]:
    approved = run_index.latest_approved(payload.ticker)
    if approved and not payload.refresh:
        report_path = approved.get("report_s3_path")
        analysis_packet_path = approved.get("analysis_packet_s3_path")
        if not report_path or not analysis_packet_path:
            raise HTTPException(status_code=404, detail="Approved run is missing artifacts")
        if payload.query_text.strip().lower() == "give me the analysis":
            return {
                "report_path": report_path,
                "analysis_packet_path": analysis_packet_path,
            }
        response = router.generate(
            model_id=payload.model_id or approved.get("model_id", settings.default_model_id),
            messages=[{"role": "user", "content": payload.query_text}],
            tools_enabled=False,
            tool_schema={},
            context_refs=[report_path, analysis_packet_path],
            run_id=approved.get("run_id", ""),
            temperature=0.2,
        )
        return response
    result = run_pipeline(
        ticker=payload.ticker,
        as_of_date=payload.as_of_date or date.today(),
        mode="interactive",
        model_id=payload.model_id or settings.default_model_id,
    )
    return {"job_id": result["run_id"], "run_id": result["run_id"], "status": result["status"]}


@app.post("/v1/model/generate")
def model_generate(payload: ModelGenerateRequest) -> Dict[str, Any]:
    return router.generate(
        model_id=payload.model_id,
        messages=payload.messages,
        tools_enabled=payload.tools_enabled,
        tool_schema=payload.tool_schema,
        context_refs=payload.context_refs,
        run_id=payload.run_id,
        temperature=payload.temperature,
    )


@app.get("/v1/models")
def list_models() -> Dict[str, Any]:
    return {"models": registry.list_models()}


@app.get("/v1/tools")
def list_tools() -> Dict[str, Any]:
    return {"tools": tool_registry.list_tools()}


@app.get("/healthz")
def healthz() -> Dict[str, str]:
    return {"status": "ok"}
