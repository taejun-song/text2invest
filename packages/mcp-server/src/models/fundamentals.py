from datetime import date, datetime
from enum import Enum
from pydantic import BaseModel, Field


class DataSourceType(str, Enum):
    YFINANCE = "yfinance"
    INVESTPY = "investpy"
    WEB_SCRAPING = "web_scraping"
    CACHE = "cache"
    UNAVAILABLE = "unavailable"


class FundamentalMetrics(BaseModel):
    pe_ratio: float | None = Field(None, description="Trailing P/E ratio")
    forward_pe: float | None = Field(None, description="Forward P/E ratio")
    market_cap: str | None = Field(None, description="Market cap with currency (e.g., '$2.8T')")
    market_cap_raw: int | None = Field(None, description="Market cap in base currency units")
    dividend_yield: float | None = Field(None, description="Dividend yield as decimal (0.02 = 2%)")
    eps: float | None = Field(None, description="Trailing EPS")
    forward_eps: float | None = Field(None, description="Forward EPS estimate")
    fifty_two_week_high: str | None = Field(None, description="52-week high with currency")
    fifty_two_week_low: str | None = Field(None, description="52-week low with currency")
    revenue: str | None = Field(None, description="Total revenue with currency")
    revenue_growth: float | None = Field(None, description="Revenue growth YoY as decimal")
    profit_margin: float | None = Field(None, description="Profit margin as decimal")


class FundamentalData(BaseModel):
    ticker: str = Field(..., description="Stock ticker symbol")
    company_name: str = Field("", description="Full company name")
    exchange: str = Field("", description="Exchange name")
    currency: str = Field("USD", description="Native currency code")
    metrics: FundamentalMetrics = Field(default_factory=FundamentalMetrics)
    source: DataSourceType = Field(DataSourceType.UNAVAILABLE, description="Data source used")
    retrieved_at: datetime = Field(default_factory=datetime.now, description="When data was retrieved")
    data_unavailable: bool = Field(False, description="True if no data could be retrieved")
    error_message: str | None = Field(None, description="Error details if unavailable")


class HistoricalMetric(BaseModel):
    period: str = Field(..., description="Period label (e.g., 'Q1 2025')")
    period_date: date = Field(..., description="Period end date")
    value: float = Field(..., description="Metric value")


class HistoricalTrend(BaseModel):
    metric_name: str = Field(..., description="Name of metric (e.g., 'P/E Ratio')")
    data_points: list[HistoricalMetric] = Field(default_factory=list)


class CachedFundamental(BaseModel):
    ticker: str = Field(..., description="Primary key")
    data: FundamentalData = Field(..., description="Cached fundamental data")
    source: DataSourceType = Field(..., description="Original data source")
    fetched_at: datetime = Field(..., description="When originally fetched")
    expires_at: datetime = Field(..., description="Cache expiration time")
