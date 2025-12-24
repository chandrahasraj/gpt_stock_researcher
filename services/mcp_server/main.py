from __future__ import annotations

import uuid
from datetime import date
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from services.mcp_server.model_registry import ModelRegistry
from services.mcp_server.model_router import ModelRouter
from services.mcp_server.tool_registry import ToolRegistry
from src.core.storage.local_storage import LocalStorage
from src.core.storage.run_index import RunIndex
from src.pipelines.stock_pipeline import run_pipeline

app = FastAPI(title="MCP Server")

registry = ModelRegistry(Path(__file__).parent / "models.yaml")
router = ModelRouter()
tool_registry = ToolRegistry()
run_index = RunIndex()
storage = LocalStorage()


class RunRequest(BaseModel):
    ticker: str
    as_of_date: Optional[date] = None
    mode: str = "interactive"
    model_id: str = "public:gpt-x"
    refresh: bool = False
    thresholds: Dict[str, Any] = {}
    max_iters: int = 1


class QueryRequest(BaseModel):
    ticker: str
    as_of_date: Optional[date] = None
    query_text: str
    refresh: bool = False
    model_id: Optional[str] = None


class ModelGenerateRequest(BaseModel):
    model_id: str
    messages: list[Dict[str, Any]]
    tools_enabled: bool = False
    tool_schema: Dict[str, Any] = {}
    context_refs: list[str] = []
    run_id: str
    temperature: float = 0.2


@app.post("/v1/run")
def run_pipeline_endpoint(payload: RunRequest) -> Dict[str, Any]:
    run_id = uuid.uuid4().hex
    result = run_pipeline(
        ticker=payload.ticker,
        as_of_date=payload.as_of_date or date.today(),
        mode=payload.mode,
        model_id=payload.model_id,
        refresh=payload.refresh,
        thresholds=payload.thresholds,
        max_iters=payload.max_iters,
    )
    return {"job_id": run_id, "run_id": result["run_id"], "status": result["status"]}


@app.get("/v1/run/{run_id}")
def get_run_status(run_id: str) -> Dict[str, Any]:
    for ticker in run_index._load().values():
        for entry in ticker.values():
            if entry.get("run_id") == run_id:
                return entry
    raise HTTPException(status_code=404, detail="Run not found")


@app.post("/v1/query")
def query(payload: QueryRequest) -> Dict[str, Any]:
    approved = run_index.latest_approved(payload.ticker)
    if approved and not payload.refresh:
        report_path = approved.get("report_s3_path")
        analysis_packet_path = approved.get("analysis_packet_s3_path")
        if payload.query_text.strip().lower() == "give me the analysis":
            return {
                "report_path": report_path,
                "analysis_packet_path": analysis_packet_path,
            }
        response = router.generate(
            model_id=payload.model_id or approved.get("model_id", "public:gpt-x"),
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
        model_id=payload.model_id or "public:gpt-x",
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
