from enum import Enum

from pydantic import BaseModel, Field

from .idea_report import Horizon, RationaleQuote, Relationship


class ConfidenceLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Sector(BaseModel):
    name: str = Field(..., min_length=1, description="Sector name (e.g., semiconductors)")
    confidence: ConfidenceLevel = Field(..., description="How confident in sector identification")
    sub_sectors: list[str] = Field(default_factory=list, description="Supply chain layers or sub-industries")


class InferredTicker(BaseModel):
    company_name: str = Field(..., description="Full company name")
    symbol: str = Field(..., pattern=r"^[A-Z0-9.\-]{1,12}$", description="Ticker symbol with exchange suffix")
    sector: str = Field(..., description="Which sector this company belongs to")
    relevance_explanation: str = Field(..., max_length=200, description="Why this company was inferred")
    confidence: ConfidenceLevel = Field(..., description="Confidence in this inference")
    market_cap_tier: str = Field(..., pattern=r"^(large|mid|small)$", description="Company size category")
    supply_chain_layer: str | None = Field(None, description="Position in value chain")
    verified: bool = Field(True, description="Whether yfinance verification succeeded")


class ExtractionOutput(BaseModel):
    cleaned_text: str = Field(..., description="Normalized text")
    language: str = Field(..., description="Detected language code")
    word_count: int = Field(..., ge=0, description="Token/word count")


class EntityOutput(BaseModel):
    companies: list[str] = Field(default_factory=list, description="Company names mentioned")
    products: list[str] = Field(default_factory=list, description="Product names mentioned")
    macro_terms: list[str] = Field(default_factory=list, description="Economic/macro terms")


class TickerMapping(BaseModel):
    company: str = Field(..., description="Company name from EntityOutput")
    symbol: str = Field(..., pattern=r"^[A-Z0-9.\-]{1,12}$", description="Resolved ticker symbol")
    confidence: float = Field(..., ge=0, le=1, description="Mapping confidence")
    reasoning: str = Field(..., description="Why this mapping")


class TickerOutput(BaseModel):
    mappings: list[TickerMapping] = Field(
        default_factory=list, description="Company-to-ticker mappings"
    )
    sectors: list[Sector] = Field(
        default_factory=list, description="Identified sectors from text analysis"
    )
    inferred_tickers: list[InferredTicker] = Field(
        default_factory=list, description="Companies inferred from sector analysis"
    )


class SectorInferenceOutput(BaseModel):
    sectors: list[Sector] = Field(default_factory=list, description="Identified sectors")
    inferred_tickers: list[InferredTicker] = Field(
        default_factory=list, description="Inferred companies per sector"
    )


class ThesisOutput(BaseModel):
    thesis: str = Field(..., description="Investment thesis")
    supporting_quotes: list[RationaleQuote] = Field(
        default_factory=list, description="Text evidence"
    )
    catalysts: list[str] = Field(default_factory=list, description="Positive triggers")
    horizon: Horizon = Field(..., description="Time horizon")


class CritiqueOutput(BaseModel):
    risks: list[str] = Field(default_factory=list, description="Risk factors")
    counter_thesis: str = Field(..., description="Opposing view")
    missing_info: list[str] = Field(default_factory=list, description="What's not in the text")


class ConfidenceOutput(BaseModel):
    score: float = Field(..., ge=0, le=1, description="Confidence score 0.0 to 1.0")
    explanation: str = Field(..., description="Calibration reasoning")
    limitations: list[str] = Field(default_factory=list, description="Known weaknesses")


class DiscoveredCompany(BaseModel):
    company_name: str = Field(..., description="Full company name")
    symbol: str = Field(..., pattern=r"^[A-Z0-9.\-]{1,12}$", description="Ticker symbol")
    relationship: Relationship = Field(..., description="Relationship type")
    primary_symbol: str = Field(..., description="Related to which primary ticker")
    depth: int = Field(..., ge=1, le=2, description="Discovery depth")
    reasoning: str = Field(..., description="Why this company is related")


class DiscoveryOutput(BaseModel):
    related_companies: list[DiscoveredCompany] = Field(
        default_factory=list, description="Discovered related companies"
    )


class TickerRecommendation(BaseModel):
    symbol: str = Field(..., description="Ticker symbol")
    signal: str = Field(..., pattern=r"^(BUY|SELL|HOLD)$", description="BUY, SELL, or HOLD")
    certainty: float = Field(..., ge=0, le=1, description="Recommendation certainty")
    rationale: str = Field(..., max_length=200, description="One-sentence explanation")
    factors: list[str] = Field(default_factory=list, description="Contributing signal factors")


class RecommendationOutput(BaseModel):
    recommendations: list[TickerRecommendation] = Field(
        default_factory=list, description="One recommendation per ticker"
    )
