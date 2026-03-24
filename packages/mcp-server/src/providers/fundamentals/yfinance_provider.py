import asyncio
import logging
from datetime import datetime, date
import yfinance as yf
from models.fundamentals import DataSourceType, FundamentalData, FundamentalMetrics, HistoricalTrend, HistoricalMetric
from providers.fundamentals.base import FundamentalsProvider
from providers.fundamentals.formatters import format_large_number, format_currency

logger = logging.getLogger(__name__)


class YFinanceProvider(FundamentalsProvider):
    name = "yfinance"
    priority = 1
    timeout = 5.0
    _backoff_delays = [1.0, 2.0, 4.0]

    async def _with_backoff(self, func, ticker: str, max_retries: int = 3):
        for attempt in range(max_retries):
            try:
                return func()
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                delay = self._backoff_delays[min(attempt, len(self._backoff_delays) - 1)]
                logger.warning(f"YFinance attempt {attempt + 1} failed for {ticker}, retrying in {delay}s: {e}")
                await asyncio.sleep(delay)
        return None

    async def get_fundamentals(self, ticker: str) -> FundamentalData | None:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            if not info or info.get("regularMarketPrice") is None:
                return None
            currency = info.get("currency", "USD")
            market_cap_raw = info.get("marketCap")
            high_52 = info.get("fiftyTwoWeekHigh")
            low_52 = info.get("fiftyTwoWeekLow")
            revenue_raw = info.get("totalRevenue")
            metrics = FundamentalMetrics(
                pe_ratio=info.get("trailingPE"),
                forward_pe=info.get("forwardPE"),
                market_cap=format_large_number(market_cap_raw, currency) if market_cap_raw else None,
                market_cap_raw=market_cap_raw,
                dividend_yield=info.get("dividendYield"),
                eps=info.get("trailingEps"),
                forward_eps=info.get("forwardEps"),
                fifty_two_week_high=format_currency(high_52, currency) if high_52 else None,
                fifty_two_week_low=format_currency(low_52, currency) if low_52 else None,
                revenue=format_large_number(revenue_raw, currency) if revenue_raw else None,
                revenue_growth=info.get("revenueGrowth"),
                profit_margin=info.get("profitMargins"),
            )
            return FundamentalData(
                ticker=ticker.upper(),
                company_name=info.get("longName") or info.get("shortName") or "",
                exchange=info.get("exchange") or "",
                currency=currency,
                metrics=metrics,
                source=DataSourceType.YFINANCE,
                retrieved_at=datetime.now(),
            )
        except Exception as e:
            logger.warning(f"YFinance failed for {ticker}: {e}")
            return None

    async def get_historical(self, ticker: str, periods: int = 4) -> list[HistoricalTrend]:
        try:
            stock = yf.Ticker(ticker)
            trends: list[HistoricalTrend] = []
            quarterly = stock.quarterly_financials
            if quarterly is not None and not quarterly.empty:
                def format_quarter(d: date) -> str:
                    q = ((d.month - 1) // 3) + 1
                    return f"Q{q} {d.year}"
                if "Total Revenue" in quarterly.index:
                    revenue_points = []
                    for col in list(quarterly.columns)[:periods]:
                        val = quarterly.loc["Total Revenue", col]
                        if val is not None and not (isinstance(val, float) and val != val):
                            period_date = col.date() if hasattr(col, "date") else date.today()
                            revenue_points.append(HistoricalMetric(
                                period=format_quarter(period_date),
                                period_date=period_date,
                                value=float(val),
                            ))
                    if revenue_points:
                        trends.append(HistoricalTrend(metric_name="Revenue", data_points=revenue_points))
                if "Net Income" in quarterly.index:
                    income_points = []
                    for col in list(quarterly.columns)[:periods]:
                        val = quarterly.loc["Net Income", col]
                        if val is not None and not (isinstance(val, float) and val != val):
                            period_date = col.date() if hasattr(col, "date") else date.today()
                            income_points.append(HistoricalMetric(
                                period=format_quarter(period_date),
                                period_date=period_date,
                                value=float(val),
                            ))
                    if income_points:
                        trends.append(HistoricalTrend(metric_name="Net Income", data_points=income_points))
            return trends
        except Exception as e:
            logger.warning(f"YFinance historical failed for {ticker}: {e}")
            return []
