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


class TechnicalIndicators(BaseModel):
    ticker: str = Field(..., description="Stock ticker symbol")
    current_price: float | None = Field(None, description="Current stock price")
    ma_50: float | None = Field(None, description="50-day simple moving average")
    ma_200: float | None = Field(None, description="200-day simple moving average")
    rsi_14: float | None = Field(None, ge=0, le=100, description="14-day RSI (0-100)")
    price_change_1w: float | None = Field(None, description="1-week price change as decimal")
    price_change_1m: float | None = Field(None, description="1-month price change as decimal")
    price_change_3m: float | None = Field(None, description="3-month price change as decimal")
    price_change_ytd: float | None = Field(None, description="Year-to-date price change as decimal")
    volume_avg_10d: int | None = Field(None, description="10-day average volume")
    retrieved_at: datetime = Field(default_factory=datetime.now, description="When data was retrieved")
    data_source: str = Field("yfinance", description="Data source used")


class ValuationComparison(BaseModel):
    ticker: str = Field(..., description="Stock ticker symbol")
    sector: str = Field("", description="Sector name")
    pe_ratio: float | None = Field(None, description="Stock P/E ratio")
    sector_pe_avg: float | None = Field(None, description="Sector average P/E ratio")
    pe_vs_sector: str | None = Field(None, description="above, below, or at")
    forward_pe: float | None = Field(None, description="Forward P/E ratio")
    sector_forward_pe_avg: float | None = Field(None, description="Sector average forward P/E")


class QuantitativeReport(BaseModel):
    ticker: str = Field(..., description="Stock ticker symbol")
    company_name: str = Field("", description="Full company name")
    fundamentals: FundamentalMetrics = Field(default_factory=FundamentalMetrics)
    technicals: TechnicalIndicators | None = Field(None, description="Technical indicators")
    valuation: ValuationComparison | None = Field(None, description="Valuation comparison")
    data_sources: list[str] = Field(default_factory=list, description="Data sources used")
    retrieved_at: datetime = Field(default_factory=datetime.now, description="When data was retrieved")
