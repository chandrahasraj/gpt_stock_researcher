from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class RunPaths(BaseModel):
    base_path: str
    raw_path: str
    parsed_path: str
    report_path: str
    trace_path: str


class RunContext(BaseModel):
    run_id: str
    ticker: str
    as_of_date: date
    created_at: datetime
    mode: str
    model_id: str
    status: str
    paths: RunPaths


class FilingRef(BaseModel):
    form: str
    period_end: Optional[date] = None
    filed_at: Optional[date] = None
    url: Optional[str] = None
    local_path: Optional[str] = None
    sha256: Optional[str] = None


class FinancialStatement(BaseModel):
    line_items: Dict[str, Any] = Field(default_factory=dict)
    currency: Optional[str] = None
    period_start: Optional[date] = None
    period_end: Optional[date] = None


class Financials(BaseModel):
    income_statement: FinancialStatement
    balance_sheet: FinancialStatement
    cash_flow: FinancialStatement
    shares: Dict[str, Any] = Field(default_factory=dict)
    notes: List[str] = Field(default_factory=list)


class DerivedMetrics(BaseModel):
    fcf: Optional[float] = None
    cfo: Optional[float] = None
    capex: Optional[float] = None
    burn_rate: Optional[float] = None
    runway_months_estimate: Optional[float] = None
    flags: List[str] = Field(default_factory=list)


class GuidanceClaims(BaseModel):
    guidance: List[str] = Field(default_factory=list)
    management_claims: List[str] = Field(default_factory=list)
    contracted_commitments: List[str] = Field(default_factory=list)
    timelines: List[str] = Field(default_factory=list)


class MarketSnapshot(BaseModel):
    price: Optional[float] = None
    market_cap: Optional[float] = None
    high_52w: Optional[float] = Field(default=None, alias="52w_high")
    low_52w: Optional[float] = Field(default=None, alias="52w_low")
    returns: Dict[str, float] = Field(default_factory=dict)


class OwnershipSnapshot(BaseModel):
    top_holders: List[Dict[str, Any]] = Field(default_factory=list)
    institutional_ownership: Optional[float] = None


class NewsArticle(BaseModel):
    title: str
    date: Optional[date] = None
    source: Optional[str] = None
    url: Optional[str] = None
    snippet: Optional[str] = None
    sha256: Optional[str] = None


class NewsBundle(BaseModel):
    articles: List[NewsArticle] = Field(default_factory=list)


class SocialBundle(BaseModel):
    themes: List[str] = Field(default_factory=list)
    bull_cases: List[str] = Field(default_factory=list)
    bear_cases: List[str] = Field(default_factory=list)
    notable_posts: List[Dict[str, Any]] = Field(default_factory=list)


class BoostersDowntrends(BaseModel):
    boosters: List[str] = Field(default_factory=list)
    downtrends: List[str] = Field(default_factory=list)


class ChecklistItemResult(BaseModel):
    check: str
    score: float
    evidence_refs: List[str] = Field(default_factory=list)


class ChecklistResult(BaseModel):
    results: List[ChecklistItemResult] = Field(default_factory=list)
    data_gaps: List[str] = Field(default_factory=list)
    overall_score: Optional[float] = None


class PersonaScore(BaseModel):
    persona: str
    score: float
    issues: List[str] = Field(default_factory=list)
    asks: List[str] = Field(default_factory=list)


class PersonaReview(BaseModel):
    persona_scores: List[PersonaScore] = Field(default_factory=list)
    approved: bool = False
    required_next_data: List[str] = Field(default_factory=list)


class InvestmentPlan(BaseModel):
    thesis_type: Optional[str] = None
    sizing_bands: List[str] = Field(default_factory=list)
    entry_triggers: List[str] = Field(default_factory=list)
    exit_triggers: List[str] = Field(default_factory=list)
    monitoring_kpis: List[str] = Field(default_factory=list)
    bull_case: Optional[str] = None
    bear_case: Optional[str] = None
    geo_reg_watchlist: List[str] = Field(default_factory=list)


class ReportBundle(BaseModel):
    report_paths: List[str] = Field(default_factory=list)
    citations_map_path: Optional[str] = None
    trace_path: Optional[str] = None


class AnalysisPacket(BaseModel):
    run_context: RunContext
    filings: List[FilingRef] = Field(default_factory=list)
    financials: Optional[Financials] = None
    derived_metrics: Optional[DerivedMetrics] = None
    guidance: Optional[GuidanceClaims] = None
    market_snapshot: Optional[MarketSnapshot] = None
    ownership_snapshot: Optional[OwnershipSnapshot] = None
    news: Optional[NewsBundle] = None
    social: Optional[SocialBundle] = None
    boosters_downtrends: Optional[BoostersDowntrends] = None
    checklist: Optional[ChecklistResult] = None
    persona_review: Optional[PersonaReview] = None
    investment_plan: Optional[InvestmentPlan] = None
    citations_map: Dict[str, str] = Field(default_factory=dict)
