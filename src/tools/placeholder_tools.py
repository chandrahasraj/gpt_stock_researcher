from __future__ import annotations

import hashlib
import uuid
from datetime import date, datetime
from typing import Any, Dict, List

from src.core.schemas.models import (
    BoostersDowntrends,
    ChecklistResult,
    DerivedMetrics,
    Financials,
    FinancialStatement,
    FilingRef,
    GuidanceClaims,
    MarketSnapshot,
    NewsBundle,
    OwnershipSnapshot,
    PersonaReview,
    ReportBundle,
    RunContext,
    RunPaths,
    SocialBundle,
)
from src.core.storage.local_storage import LocalStorage


def _sha256(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def init_run_context(ticker: str, as_of_date: date, mode: str, model_id: str, storage: LocalStorage) -> RunContext:
    run_id = uuid.uuid4().hex
    base_path = f"{ticker}/{as_of_date}/{run_id}"
    paths = RunPaths(
        base_path=base_path,
        raw_path=f"{base_path}/raw",
        parsed_path=f"{base_path}/parsed",
        report_path=f"{base_path}/report",
        trace_path=f"{base_path}/trace",
    )
    storage.ensure_dir(paths.raw_path)
    storage.ensure_dir(paths.parsed_path)
    storage.ensure_dir(paths.report_path)
    storage.ensure_dir(paths.trace_path)
    return RunContext(
        run_id=run_id,
        ticker=ticker,
        as_of_date=as_of_date,
        created_at=datetime.utcnow(),
        mode=mode,
        model_id=model_id,
        status="initialized",
        paths=paths,
    )


def fetch_sec_filings(ticker: str, forms: List[str], limit: int = 3) -> List[FilingRef]:
    filings = []
    for form in forms[:limit]:
        filings.append(
            FilingRef(
                form=form,
                period_end=None,
                filed_at=None,
                url=None,
                local_path=None,
                sha256=_sha256(f"{ticker}-{form}"),
            )
        )
    return filings


def parse_filing_financials(_filing_local_path: str) -> Financials:
    empty_statement = FinancialStatement(
        line_items={},
        currency=None,
        period_start=None,
        period_end=None,
    )
    return Financials(
        income_statement=empty_statement,
        balance_sheet=empty_statement,
        cash_flow=empty_statement,
        shares={},
        notes=["Placeholder financials; parsing not implemented."],
    )


def compute_derived_metrics(_financials: Financials) -> DerivedMetrics:
    return DerivedMetrics(
        fcf=None,
        cfo=None,
        capex=None,
        burn_rate=None,
        runway_months_estimate=None,
        flags=["Derived metrics not computed; missing inputs."],
    )


def fetch_investor_materials(ticker: str, types: List[str]) -> Dict[str, Any]:
    docs = []
    for doc_type in types:
        docs.append(
            {
                "type": doc_type,
                "url": None,
                "local_path": None,
                "sha256": _sha256(f"{ticker}-{doc_type}"),
            }
        )
    return {"docs": docs}


def extract_guidance_and_claims(_docs: List[Dict[str, Any]]) -> GuidanceClaims:
    return GuidanceClaims(
        guidance=["Guidance extraction placeholder."],
        management_claims=[],
        contracted_commitments=[],
        timelines=[],
    )


def fetch_market_data(_ticker: str, _window: str) -> MarketSnapshot:
    return MarketSnapshot(price=None, market_cap=None, high_52w=None, low_52w=None, returns={})


def fetch_ownership_and_holders(_ticker: str) -> OwnershipSnapshot:
    return OwnershipSnapshot(top_holders=[], institutional_ownership=None)


def fetch_news(_ticker: str, _days_back: int, _recency_weighted: bool) -> NewsBundle:
    return NewsBundle(articles=[])


def fetch_social_sentiment(_ticker: str, _platforms: List[str], _days_back: int) -> SocialBundle:
    return SocialBundle(themes=[], bull_cases=[], bear_cases=[], notable_posts=[])


def build_boosters_downtrends(*_args: Any, **_kwargs: Any) -> BoostersDowntrends:
    return BoostersDowntrends(boosters=[], downtrends=[])


def run_critical_checklist(*_args: Any, **_kwargs: Any) -> ChecklistResult:
    return ChecklistResult(results=[], data_gaps=["Checklist not implemented"], overall_score=0.0)


def multi_persona_review(*_args: Any, **_kwargs: Any) -> PersonaReview:
    return PersonaReview(persona_scores=[], approved=False, required_next_data=["Persona review not implemented"])


def generate_investment_plan(*_args: Any, **_kwargs: Any) -> Dict[str, Any]:
    return {
        "thesis_type": "",
        "sizing_bands": [],
        "entry_triggers": [],
        "exit_triggers": [],
        "monitoring_kpis": [],
        "bull_case": "",
        "bear_case": "",
        "geo_reg_watchlist": [],
    }


def render_report(storage: LocalStorage, base_path: str, analysis_packet: Dict[str, Any]) -> ReportBundle:
    report_path = storage.write_text(
        f"{base_path}/report/final_report.md",
        "# Stock Analysis Report\n\nReport rendering placeholder.",
    )
    citations_path = storage.write_json(f"{base_path}/report/citations_map.json", {})
    trace_path = storage.write_json(f"{base_path}/trace/trace.json", {"note": "trace placeholder"})
    return ReportBundle(report_paths=[report_path], citations_map_path=citations_path, trace_path=trace_path)
