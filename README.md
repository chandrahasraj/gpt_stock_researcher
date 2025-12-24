# Stock Analysis Agent

This project scaffolds a stock analysis pipeline, an MCP-compatible server, and supporting tooling for daily watchlist runs. It is designed to evolve into a filings-first, evidence-backed analysis system with deterministic tools and model routing.

## Repository Layout

```
services/mcp_server/     # FastAPI MCP server
src/core/                # schemas, storage, utils, citations
src/clients/             # external data providers (pluggable)
src/tools/               # deterministic tool implementations
src/pipelines/           # stock pipeline state machine
scripts/                 # watchlist runner and utilities
infra/                   # AWS CDK (placeholder)
```

## Quickstart (local)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .

# Run the MCP server
uvicorn services.mcp_server.main:app --reload

# Run a pipeline for a ticker
python -m src.pipelines.stock_pipeline --ticker ASTS --mode interactive --model-id public:gpt-x
```

## Infrastructure (AWS CDK)

Infrastructure lives under `infra/` and deploys an ECS Fargate Spot service for the MCP server, a scheduled pipeline runner, and an S3 bucket for run artifacts.

```bash
cd infra
python -m venv .venv
source .venv/bin/activate
pip install -e ..[dev]

# Set your AWS credentials before running CDK.
cdk synth
cdk deploy \
  --parameters ContainerImage=<image-uri> \
  --parameters ServerCommand="uvicorn services.mcp_server.main:app --host 0.0.0.0 --port 8000" \
  --parameters PipelineCommand="python -m src.pipelines.stock_pipeline --ticker ASTS --mode batch" \
  --parameters PipelineSchedule="rate(1 day)"
```

## Notes
- The implementation is intentionally minimal and focused on structure.
- Tools return structured JSON and write artifacts to local storage under `runs/`.
- A mock RunIndex is stored at `runs/run_index.json` for local development.
