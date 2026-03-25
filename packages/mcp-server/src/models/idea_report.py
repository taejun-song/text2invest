from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class Horizon(str, Enum):
    SHORT = "short"
    MEDIUM = "medium"
    LONG = "long"


class Provider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"
    NRP = "nrp"


class Signal(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class SearchDepth(str, Enum):
    FOCUSED = "focused"
    STANDARD = "standard"
    EXPANDED = "expanded"


class Relationship(str, Enum):
    COMPETITOR = "competitor"
    SUPPLIER = "supplier"
    CUSTOMER = "customer"
    SECTOR_PEER = "sector_peer"
    PARENT_SUBSIDIARY = "parent_subsidiary"


class Rating(str, Enum):
    USEFUL = "useful"
    NOT_USEFUL = "not_useful"


class Source(BaseModel):
    url: str = Field(..., description="Page URL")
    title: str = Field(..., description="Page title")


class Recommendation(BaseModel):
    signal: Signal = Field(..., description="BUY, SELL, or HOLD")
    certainty: float = Field(..., ge=0, le=1, description="Recommendation certainty")
    rationale: str = Field(..., max_length=200, description="One-sentence explanation")
    factors: list[str] = Field(default_factory=list, max_length=5, description="Key signal factors")


class Ticker(BaseModel):
    symbol: str = Field(..., pattern=r"^[A-Z0-9.\-]{1,12}$", description="Stock ticker symbol")
    company_name: str = Field(..., description="Full company name")
    confidence: float = Field(..., ge=0, le=1, description="Mapping certainty (0.0 to 1.0)")
    recommendation: Recommendation | None = Field(None, description="BUY/SELL/HOLD recommendation")


class RelatedTicker(BaseModel):
    symbol: str = Field(..., pattern=r"^[A-Z0-9.\-]{1,12}$", description="Ticker symbol")
    company_name: str = Field(..., description="Full company name")
    relationship: Relationship = Field(..., description="Relationship to primary ticker")
    primary_symbol: str = Field(..., description="Which primary ticker this relates to")
    depth: int = Field(..., ge=1, le=2, description="Discovery depth level")
    recommendation: Recommendation | None = Field(None, description="BUY/SELL/HOLD recommendation")


class InferredTickerReport(BaseModel):
    symbol: str = Field(..., pattern=r"^[A-Z0-9.\-]{1,12}$", description="Ticker symbol")
    company_name: str = Field(..., description="Full company name")
    sector: str = Field(..., description="Sector this company belongs to")
    relevance_explanation: str = Field(..., max_length=200, description="Why this company was inferred")
    confidence: str = Field(..., pattern=r"^(high|medium)$", description="Inference confidence level")
    market_cap_tier: str = Field(..., pattern=r"^(large|mid|small)$", description="Company size")
    supply_chain_layer: str | None = Field(None, description="Position in value chain")
    verified: bool = Field(True, description="Whether ticker was verified via market data")


class SectorReport(BaseModel):
    name: str = Field(..., description="Sector name")
    confidence: str = Field(..., pattern=r"^(high|medium)$", description="Identification confidence")
    sub_sectors: list[str] = Field(default_factory=list, description="Sub-sectors or supply chain layers")


class RationaleQuote(BaseModel):
    quote: str = Field(..., description="Exact text from selection")
    start_offset: int = Field(..., ge=0, description="Character offset from start")
    end_offset: int = Field(..., ge=1, description="Character offset to end")

    @field_validator("end_offset")
    @classmethod
    def end_after_start(cls, v: int, info) -> int:
        if "start_offset" in info.data and v <= info.data["start_offset"]:
            raise ValueError("end_offset must be greater than start_offset")
        return v


class ProviderMeta(BaseModel):
    provider: Provider = Field(..., description="LLM provider name")
    model: str = Field(..., description="Model identifier")
    temperature: float = Field(..., ge=0, le=2, description="Generation temperature")
    pipeline_duration_ms: int = Field(..., ge=0, description="Total processing time in ms")


class IdeaReport(BaseModel):
    id: UUID = Field(..., description="Unique identifier")
    created_at: datetime = Field(..., description="Creation timestamp")
    source: Source = Field(..., description="Origin webpage information")
    selection_text: str = Field(
        ..., min_length=20, max_length=8000, description="Original selected text"
    )
    tickers: list[Ticker] = Field(default_factory=list, description="Identified securities")
    thesis: str = Field(..., description="Investment thesis statement")
    executive_summary: list[str] = Field(
        ..., min_length=1, max_length=3, description="Max 3 bullet points"
    )
    rationale_quotes: list[RationaleQuote] = Field(
        default_factory=list, description="Supporting text excerpts"
    )
    catalysts: list[str] = Field(default_factory=list, description="Potential positive triggers")
    risks: list[str] = Field(default_factory=list, description="Identified risk factors")
    counter_thesis: str = Field(..., description="Opposing viewpoint")
    horizon: Horizon = Field(..., description="Time horizon")
    confidence_score: float | None = Field(None, ge=0, le=1, description="Overall confidence (deprecated)")
    confidence_explanation: str | None = Field(None, description="Why this confidence level (deprecated)")
    quantitative_data: list[Any] = Field(default_factory=list, description="Quantitative metrics per ticker")
    limitations: list[str] = Field(default_factory=list, description="Known limitations")
    provider_meta: ProviderMeta = Field(..., description="LLM provider information")
    news_context: list[Any] | None = Field(None, description="News items from News Agent")
    fundamentals_summary: list[Any] | None = Field(None, description="Financial data from Fundamentals Agent")
    cross_reference_analysis: Any | None = Field(None, description="Cross-agent comparison")
    macro_context: Any | None = Field(None, description="Macro-economic context")
    agent_attributions: dict[str, list[str]] | None = Field(None, description="Section to agent attribution")
    communication_log: Any | None = Field(None, description="Inter-agent communication record")
    thinking_output: dict[str, Any] | None = Field(None, description="Per-agent thinking/reasoning content")
    related_tickers: list[RelatedTicker] = Field(default_factory=list, description="Discovered related tickers")
    search_depth: str | None = Field(None, description="Search depth used for this report")
    sectors: list[SectorReport] = Field(default_factory=list, description="Identified sectors from text")
    inferred_tickers: list[InferredTickerReport] = Field(default_factory=list, description="Tickers inferred from sector analysis")
    disclaimer: str = Field(
        default="AI-generated analysis for educational purposes only. Not professional financial advice.",
        description="Recommendation disclaimer",
    )


class UserSettings(BaseModel):
    provider: Provider = Field(..., description="LLM provider")
    model: str = Field(..., description="Model identifier")
    api_key: str | None = Field(None, description="API key for cloud providers")
    base_url: str | None = Field(None, description="Base URL for Ollama or NRP.ai")
    temperature: float = Field(0.7, ge=0, le=2, description="Generation temperature")
    pii_redaction: bool = Field(True, description="Redact emails and phone numbers")
    web_lookup: bool = Field(False, description="Allow web searches")
    agent_configs: list[Any] | None = Field(None, description="Per-agent configuration")
    thinking_mode: bool = Field(False, description="Enable LLM thinking/reasoning mode")
    output_language: str | None = Field(None, description="Output language locale code (e.g., ko, ja)")
    search_depth: SearchDepth = Field(SearchDepth.STANDARD, description="Related ticker discovery depth")

    @field_validator("api_key")
    @classmethod
    def api_key_required_for_cloud(cls, v: str | None, info) -> str | None:
        if "provider" in info.data:
            provider = info.data["provider"]
            if provider in (Provider.OPENAI, Provider.ANTHROPIC, Provider.NRP) and not v:
                raise ValueError(f"api_key is required for {provider}")
        return v

    @field_validator("base_url")
    @classmethod
    def base_url_required_for_ollama(cls, v: str | None, info) -> str | None:
        if "provider" in info.data:
            provider = info.data["provider"]
            if provider == Provider.OLLAMA and not v:
                raise ValueError("base_url is required for Ollama")
        return v


class Evaluation(BaseModel):
    idea_id: UUID = Field(..., description="Reference to IdeaReport")
    rating: Rating = Field(..., description="User rating")
    notes: str | None = Field(None, description="Optional explanation")
    created_at: datetime = Field(..., description="Rating timestamp")


class UserTicker(BaseModel):
    symbol: str = Field(..., pattern=r"^[A-Z0-9.\-]{1,12}$", description="Ticker symbol")
    company_name: str | None = Field(None, description="Optional company name")


class IdeaRequest(BaseModel):
    selection_text: str = Field(
        ..., min_length=20, max_length=8000, description="Text selected by user"
    )
    url: str = Field(..., description="Source page URL")
    title: str = Field(..., description="Source page title")
    user_settings: UserSettings = Field(..., description="User configuration")
    user_tickers: list[UserTicker] = Field(default_factory=list, description="User-provided tickers to include")
