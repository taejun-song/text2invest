import asyncio
import logging
from datetime import datetime, date
import yfinance as yf
from models.fundamentals import DataSourceType, FundamentalData, FundamentalMetrics, HistoricalTrend, HistoricalMetric, TechnicalIndicators
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

    async def get_technical_indicators(self, ticker: str) -> TechnicalIndicators | None:
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="1y")
            if hist.empty:
                return None
            current_price = float(hist["Close"].iloc[-1])
            ma_50 = self._calculate_moving_average(hist, 50)
            ma_200 = self._calculate_moving_average(hist, 200)
            rsi_14 = self._calculate_rsi(hist, 14)
            price_change_1w = self._calculate_price_change(hist, 5)
            price_change_1m = self._calculate_price_change(hist, 21)
            price_change_3m = self._calculate_price_change(hist, 63)
            price_change_ytd = self._calculate_ytd_change(hist)
            volume_avg = int(hist["Volume"].tail(10).mean()) if len(hist) >= 10 else None
            return TechnicalIndicators(
                ticker=ticker.upper(),
                current_price=current_price,
                ma_50=ma_50,
                ma_200=ma_200,
                rsi_14=rsi_14,
                price_change_1w=price_change_1w,
                price_change_1m=price_change_1m,
                price_change_3m=price_change_3m,
                price_change_ytd=price_change_ytd,
                volume_avg_10d=volume_avg,
                retrieved_at=datetime.now(),
            )
        except Exception as e:
            logger.warning(f"YFinance technical failed for {ticker}: {e}")
            return None

    def _calculate_moving_average(self, hist, period: int) -> float | None:
        if len(hist) < period:
            return None
        return float(hist["Close"].tail(period).mean())

    def _calculate_rsi(self, hist, period: int = 14) -> float | None:
        if len(hist) < period + 1:
            return None
        delta = hist["Close"].diff()
        gain = delta.where(delta > 0, 0.0)
        loss = (-delta).where(delta < 0, 0.0)
        avg_gain = gain.ewm(span=period, adjust=False).mean().iloc[-1]
        avg_loss = loss.ewm(span=period, adjust=False).mean().iloc[-1]
        if avg_loss == 0:
            return 100.0
        rs = avg_gain / avg_loss
        return float(100 - (100 / (1 + rs)))

    def _calculate_price_change(self, hist, days: int) -> float | None:
        if len(hist) < days + 1:
            return None
        current = hist["Close"].iloc[-1]
        past = hist["Close"].iloc[-days - 1]
        return float((current - past) / past)

    def _calculate_ytd_change(self, hist) -> float | None:
        current_year = datetime.now().year
        ytd_data = hist[hist.index.year == current_year]
        if len(ytd_data) < 2:
            return None
        first_price = ytd_data["Close"].iloc[0]
        current_price = ytd_data["Close"].iloc[-1]
        return float((current_price - first_price) / first_price)

    async def get_sector_info(self, ticker: str) -> dict | None:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            if not info:
                return None
            return {
                "sector": info.get("sector", ""),
                "industry": info.get("industry", ""),
                "sector_pe": info.get("sectorPe"),
            }
        except Exception as e:
            logger.warning(f"YFinance sector info failed for {ticker}: {e}")
            return None
