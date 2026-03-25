from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


class DataSource(str, Enum):
    WEB_SEARCH = "web_search"
    NEWS_SEARCH = "news_search"
    LLM_KNOWLEDGE = "llm_knowledge"


class Sentiment(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class MessageType(str, Enum):
    FINDING = "finding"
    QUERY = "query"
    CHALLENGE = "challenge"
    RESPONSE = "response"


class NewsItem(BaseModel):
    headline: str = Field(..., description="News article headline")
    source: str = Field(..., description="Publication or website name")
    url: str = Field(..., description="Link to the article")
    published_date: str = Field(..., description="Publication date")
    sentiment: Sentiment = Field(..., description="Article sentiment")
    relevance_score: float = Field(..., ge=0, le=1, description="Relevance to thesis (0.0 to 1.0)")
    summary: str = Field(..., description="2-3 sentence summary")
    data_source: DataSource = Field(..., description="How this data was obtained")


class FinancialMetric(BaseModel):
    name: str = Field(..., description="Metric name (e.g., Revenue, P/E Ratio)")
    value: str = Field(..., description="Metric value as formatted string")
    period: str | None = Field(None, description="Reporting period (e.g., FY2025)")


class FundamentalsSnapshot(BaseModel):
    ticker: str = Field(..., description="Stock ticker symbol")
    company_name: str = Field(..., description="Full company name")
    exchange: str = Field("", description="Exchange name")
    currency: str = Field("USD", description="Native currency code")
    metrics: list[FinancialMetric] = Field(default_factory=list, description="Key financial metrics")
    fundamental_data: dict | None = Field(None, description="Structured fundamental data from provider")
    technical_indicators: dict | None = Field(None, description="Technical analysis data")
    historical_trends: list[dict] = Field(default_factory=list, description="Historical trend data")
    data_source: DataSource = Field(..., description="How this data was obtained")
    retrieved_at: datetime = Field(..., description="When data was retrieved")


class Divergence(BaseModel):
    topic: str = Field(..., description="What the divergence is about")
    finding_a: str = Field(..., description="First agent's conclusion")
    source_a: str = Field(..., description="Agent ID that produced finding_a")
    finding_b: str = Field(..., description="Second agent's conclusion")
    source_b: str = Field(..., description="Agent ID that produced finding_b")
    explanation: str = Field(..., description="Synthesis Agent's analysis of the divergence")


class CrossReferenceAnalysis(BaseModel):
    convergences: list[str] = Field(default_factory=list, description="Findings where agents agree")
    divergences: list[Divergence] = Field(default_factory=list, description="Findings where agents disagree")
    deduplicated_risks: list[str] = Field(default_factory=list, description="Risks reported once")


class MacroContext(BaseModel):
    sector: str = Field(..., description="Relevant sector/industry")
    sector_trends: list[str] = Field(default_factory=list, description="Current sector-level trends")
    economic_indicators: list[str] = Field(default_factory=list, description="Relevant economic indicators")
    headwinds: list[str] = Field(default_factory=list, description="Negative macro factors")
    tailwinds: list[str] = Field(default_factory=list, description="Positive macro factors")
    data_source: DataSource = Field(..., description="How this data was obtained")


class AgentMessage(BaseModel):
    id: UUID = Field(..., description="Unique message identifier")
    sender: str = Field(..., description="Sending agent ID")
    recipient: str = Field(..., description="Receiving agent ID or 'broadcast'")
    message_type: MessageType = Field(..., description="Type of message")
    content: dict = Field(default_factory=dict, description="Structured message payload")
    timestamp: datetime = Field(..., description="When message was sent")
    round_number: int = Field(..., ge=1, le=3, description="Communication round (1-3)")


class CommunicationLog(BaseModel):
    id: UUID = Field(..., description="Unique log identifier")
    messages: list[AgentMessage] = Field(default_factory=list, description="All messages chronologically")
    total_rounds: int = Field(..., ge=0, le=3, description="Number of rounds used")
    duration_ms: int = Field(..., ge=0, description="Total wall-clock time for collaboration")


class AgentConfig(BaseModel):
    agent_id: str = Field(..., description="Agent identifier (e.g., news_agent)")
    enabled: bool = Field(True, description="Whether agent participates in analysis")
    use_external_data: bool = Field(True, description="Whether agent can make web searches")


# Agent Output Models (Pipeline Intermediaries)

class NewsAgentOutput(BaseModel):
    news_items: list[NewsItem] = Field(default_factory=list, description="Discovered news articles")
    overall_sentiment: Sentiment = Field(Sentiment.NEUTRAL, description="Aggregate sentiment")
    key_themes: list[str] = Field(default_factory=list, description="Recurring themes in news")
    confidence_score: float = Field(0.5, ge=0, le=1, description="Agent confidence in findings")


class FundamentalsAgentOutput(BaseModel):
    snapshots: list[FundamentalsSnapshot] = Field(default_factory=list, description="Financial data per ticker")
    assessment: str = Field("", description="Summary assessment of financial health")
    confidence_score: float = Field(0.5, ge=0, le=1, description="Agent confidence in findings")


class RiskAgentOutput(BaseModel):
    risks: list[str] = Field(default_factory=list, description="Identified risk factors")
    risk_sources: dict[str, list[str]] = Field(default_factory=dict, description="Risk to source agent IDs")
    severity_ranking: list[str] = Field(default_factory=list, description="Risks ordered by severity")
    confidence_score: float = Field(0.5, ge=0, le=1, description="Agent confidence in findings")


class MacroAgentOutput(BaseModel):
    context: MacroContext | None = Field(None, description="Macro-economic analysis")
    impact_assessment: str = Field("", description="How macro factors affect thesis")
    confidence_score: float = Field(0.5, ge=0, le=1, description="Agent confidence in findings")


class SynthesisAgentOutput(BaseModel):
    enriched_thesis: str = Field("", description="Thesis revised with all agent inputs")
    enriched_executive_summary: list[str] = Field(default_factory=list, description="Updated summary (max 3)")
    cross_reference: CrossReferenceAnalysis | None = Field(None, description="Cross-agent comparison")
    agent_attributions: dict[str, list[str]] = Field(default_factory=dict, description="Section to agent attribution")
