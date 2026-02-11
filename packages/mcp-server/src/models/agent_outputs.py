from pydantic import BaseModel, Field

from .idea_report import Horizon, RationaleQuote


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
    symbol: str = Field(..., pattern=r"^[A-Z]{1,5}$", description="Resolved ticker symbol")
    confidence: float = Field(..., ge=0, le=1, description="Mapping confidence")
    reasoning: str = Field(..., description="Why this mapping")


class TickerOutput(BaseModel):
    mappings: list[TickerMapping] = Field(
        default_factory=list, description="Company-to-ticker mappings"
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
