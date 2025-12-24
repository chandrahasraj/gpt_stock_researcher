from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import date
from typing import Any, Dict, Optional

from src.core.schemas.models import AnalysisPacket
from src.core.storage.local_storage import LocalStorage
from src.core.storage.run_index import RunIndex
from src.core.storage.training_writer import TrainingArtifactWriter
from src.tools import placeholder_tools


def run_pipeline(
    ticker: str,
    as_of_date: date,
    mode: str,
    model_id: str,
    refresh: bool = False,
    thresholds: Optional[Dict[str, Any]] = None,
    max_iters: int = 1,
) -> Dict[str, Any]:
    storage = LocalStorage()
    run_index = RunIndex()

    run_context = placeholder_tools.init_run_context(ticker, as_of_date, mode, model_id, storage)
    filings = placeholder_tools.fetch_sec_filings(ticker, ["10-Q", "10-K", "8-K"], limit=3)
    financials = placeholder_tools.parse_filing_financials("placeholder")
    derived_metrics = placeholder_tools.compute_derived_metrics(financials)
    investor_materials = placeholder_tools.fetch_investor_materials(
        ticker, ["earnings_release", "deck", "guidance"]
    )
    guidance = placeholder_tools.extract_guidance_and_claims(investor_materials["docs"])
    market_snapshot = placeholder_tools.fetch_market_data(ticker, window="1y")
    ownership_snapshot = placeholder_tools.fetch_ownership_and_holders(ticker)
    news = placeholder_tools.fetch_news(ticker, days_back=30, recency_weighted=True)
    social = placeholder_tools.fetch_social_sentiment(ticker, platforms=["reddit", "stocktwits", "x"], days_back=14)

    analysis_packet = AnalysisPacket(
        run_context=run_context,
        filings=filings,
        financials=financials,
        derived_metrics=derived_metrics,
        guidance=guidance,
        market_snapshot=market_snapshot,
        ownership_snapshot=ownership_snapshot,
        news=news,
        social=social,
    )

    boosters_downtrends = placeholder_tools.build_boosters_downtrends(
        financials, guidance, news, social
    )
    checklist = placeholder_tools.run_critical_checklist(analysis_packet.model_dump(), checklist_version="v1")
    persona_review = placeholder_tools.multi_persona_review(
        analysis_packet.model_dump(), checklist, personas=["hf_pm", "sell_side", "trader", "credit"], thresholds=thresholds
    )

    analysis_packet.boosters_downtrends = boosters_downtrends
    analysis_packet.checklist = checklist
    analysis_packet.persona_review = persona_review

    iteration = 0
    while iteration < max_iters and (checklist.data_gaps or not persona_review.approved):
        iteration += 1
        checklist = placeholder_tools.run_critical_checklist(analysis_packet.model_dump(), checklist_version="v1")
        persona_review = placeholder_tools.multi_persona_review(
            analysis_packet.model_dump(), checklist, personas=["hf_pm", "sell_side", "trader", "credit"], thresholds=thresholds
        )
        analysis_packet.checklist = checklist
        analysis_packet.persona_review = persona_review
        if persona_review.approved:
            break

    investment_plan = placeholder_tools.generate_investment_plan(
        analysis_packet.model_dump(), persona_review, risk_profile="speculative"
    )
    analysis_packet.investment_plan = investment_plan

    parsed_path = f"{run_context.paths.parsed_path}/analysis_packet.json"
    storage.write_json(parsed_path, analysis_packet.model_dump())

    report_bundle = placeholder_tools.render_report(storage, run_context.paths.base_path, analysis_packet.model_dump())

    status = "approved" if persona_review.approved else "blocked"
    run_index.put(
        ticker,
        str(as_of_date),
        run_context.run_id,
        {
            "run_id": run_context.run_id,
            "status": status,
            "approved": persona_review.approved,
            "model_id": model_id,
            "created_at": run_context.created_at.isoformat(),
            "report_s3_path": report_bundle.report_paths[0],
            "analysis_packet_s3_path": storage.path(parsed_path),
            "citations_map_s3_path": report_bundle.citations_map_path,
        },
    )

    training_writer = TrainingArtifactWriter(storage)
    training_writer.write(
        f"training/{ticker}/{as_of_date}/{run_context.run_id}",
        {
            "analysis_packet": analysis_packet.model_dump(),
            "draft_report": "",
            "persona_reviews": persona_review.model_dump(),
            "final_report": "Report rendering placeholder.",
            "diffs": {},
            "metadata": {
                "model_id": model_id,
                "thresholds": thresholds or {},
                "approved": persona_review.approved,
            },
        },
    )

    return {
        "run_id": run_context.run_id,
        "status": status,
        "report_path": report_bundle.report_paths[0],
        "analysis_packet_path": storage.path(parsed_path),
        "citations_map_path": report_bundle.citations_map_path,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the stock analysis pipeline")
    parser.add_argument("--ticker", required=True)
    parser.add_argument("--as-of-date", default=str(date.today()))
    parser.add_argument("--mode", default="interactive")
    parser.add_argument("--model-id", default="public:gpt-x")
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument("--max-iters", type=int, default=1)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = run_pipeline(
        ticker=args.ticker,
        as_of_date=date.fromisoformat(args.as_of_date),
        mode=args.mode,
        model_id=args.model_id,
        refresh=args.refresh,
        max_iters=args.max_iters,
    )
    print(result)


if __name__ == "__main__":
    main()
