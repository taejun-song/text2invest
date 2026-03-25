import asyncio
import logging
from datetime import datetime
from models.fundamentals import DataSourceType, FundamentalData, HistoricalTrend, TechnicalIndicators, QuantitativeReport, ValuationComparison
from providers.fundamentals.base import FundamentalsProvider
from providers.fundamentals.yfinance_provider import YFinanceProvider
from providers.fundamentals.investpy_provider import InvestpyProvider
from providers.fundamentals.scraper_provider import ScraperProvider

logger = logging.getLogger(__name__)


class FundamentalsService:
    def __init__(self, use_cache: bool = True):
        self.providers: list[FundamentalsProvider] = [
            YFinanceProvider(),
            InvestpyProvider(),
            ScraperProvider(),
        ]
        self.providers.sort(key=lambda p: p.priority)
        self.use_cache = use_cache
        self._cache = None

    def _get_cache(self):
        if self._cache is None:
            try:
                from storage.fundamentals_cache import get_fundamentals_cache
                self._cache = get_fundamentals_cache()
            except Exception as e:
                logger.warning(f"Cache unavailable: {e}")
        return self._cache

    async def get_fundamentals(self, ticker: str, refresh: bool = False) -> FundamentalData:
        ticker = ticker.upper().strip()
        cache = self._get_cache()
        if self.use_cache and cache and not refresh:
            try:
                cached = await cache.get_cached(ticker)
                if cached:
                    logger.info(f"Cache hit for {ticker}")
                    return cached
            except Exception as e:
                logger.warning(f"Cache lookup failed for {ticker}: {e}")
        result = await self._fetch_from_providers(ticker)
        if self.use_cache and cache and not result.data_unavailable:
            try:
                await cache.set_cached(ticker, result)
            except Exception as e:
                logger.warning(f"Cache write failed for {ticker}: {e}")
        return result

    async def _fetch_from_providers(self, ticker: str) -> FundamentalData:
        for provider in self.providers:
            if not provider.supports_market(ticker):
                continue
            try:
                result = await asyncio.wait_for(
                    provider.get_fundamentals(ticker),
                    timeout=provider.timeout,
                )
                if result and not result.data_unavailable:
                    logger.info(f"Got fundamentals for {ticker} from {provider.name}")
                    return result
            except asyncio.TimeoutError:
                logger.warning(f"{provider.name} timed out for {ticker}")
            except Exception as e:
                logger.warning(f"{provider.name} error for {ticker}: {e}")
        return FundamentalData(
            ticker=ticker,
            source=DataSourceType.UNAVAILABLE,
            data_unavailable=True,
            error_message="No provider could retrieve data",
            retrieved_at=datetime.now(),
        )

    async def get_fundamentals_batch(self, tickers: list[str], refresh: bool = False) -> dict[str, FundamentalData]:
        tasks = [self.get_fundamentals(t, refresh=refresh) for t in tickers]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        output: dict[str, FundamentalData] = {}
        for ticker, result in zip(tickers, results):
            if isinstance(result, Exception):
                output[ticker] = FundamentalData(
                    ticker=ticker,
                    source=DataSourceType.UNAVAILABLE,
                    data_unavailable=True,
                    error_message=str(result),
                    retrieved_at=datetime.now(),
                )
            else:
                output[ticker] = result
        return output

    async def get_cache_info(self, ticker: str) -> dict | None:
        cache = self._get_cache()
        if cache:
            return await cache.get_cache_info(ticker)
        return None

    async def clear_cache(self):
        cache = self._get_cache()
        if cache:
            await cache.clear_all()

    async def get_historical(self, ticker: str, periods: int = 4) -> list[HistoricalTrend]:
        ticker = ticker.upper().strip()
        cache = self._get_cache()
        if self.use_cache and cache:
            try:
                cached = await cache.get_historical_cached(ticker)
                if cached:
                    logger.info(f"Historical cache hit for {ticker}")
                    return cached
            except Exception as e:
                logger.warning(f"Historical cache lookup failed: {e}")
        for provider in self.providers:
            if not provider.supports_market(ticker):
                continue
            try:
                result = await asyncio.wait_for(
                    provider.get_historical(ticker, periods),
                    timeout=provider.timeout,
                )
                if result:
                    logger.info(f"Got historical for {ticker} from {provider.name}")
                    if self.use_cache and cache:
                        try:
                            await cache.set_historical_cached(ticker, result)
                        except Exception as e:
                            logger.warning(f"Historical cache write failed: {e}")
                    return result
            except asyncio.TimeoutError:
                logger.warning(f"{provider.name} historical timed out for {ticker}")
            except Exception as e:
                logger.warning(f"{provider.name} historical error for {ticker}: {e}")
        return []

    async def get_technical_indicators(self, ticker: str, refresh: bool = False) -> TechnicalIndicators | None:
        ticker = ticker.upper().strip()
        cache = self._get_cache()
        if self.use_cache and cache and not refresh:
            try:
                cached = await cache.get_technical_cached(ticker)
                if cached:
                    logger.info(f"Technical cache hit for {ticker}")
                    return cached
            except Exception as e:
                logger.warning(f"Technical cache lookup failed: {e}")
        yf_provider = self.providers[0]
        if hasattr(yf_provider, "get_technical_indicators"):
            try:
                result = await asyncio.wait_for(
                    yf_provider.get_technical_indicators(ticker),
                    timeout=yf_provider.timeout + 5,
                )
                if result:
                    logger.info(f"Got technical for {ticker}")
                    if self.use_cache and cache:
                        try:
                            await cache.set_technical_cached(ticker, result, ttl_hours=1)
                        except Exception as e:
                            logger.warning(f"Technical cache write failed: {e}")
                    return result
            except asyncio.TimeoutError:
                logger.warning(f"Technical indicators timed out for {ticker}")
            except Exception as e:
                logger.warning(f"Technical indicators error for {ticker}: {e}")
        return None

    async def get_valuation_comparison(self, ticker: str) -> ValuationComparison | None:
        ticker = ticker.upper().strip()
        yf_provider = self.providers[0]
        if hasattr(yf_provider, "get_sector_info"):
            try:
                sector_info = await yf_provider.get_sector_info(ticker)
                fundamentals = await self.get_fundamentals(ticker)
                if sector_info and fundamentals and not fundamentals.data_unavailable:
                    pe = fundamentals.metrics.pe_ratio
                    sector_pe = sector_info.get("sector_pe")
                    pe_vs = None
                    if pe and sector_pe:
                        if pe > sector_pe * 1.05:
                            pe_vs = "above"
                        elif pe < sector_pe * 0.95:
                            pe_vs = "below"
                        else:
                            pe_vs = "at"
                    return ValuationComparison(
                        ticker=ticker,
                        sector=sector_info.get("sector", ""),
                        pe_ratio=pe,
                        sector_pe_avg=sector_pe,
                        pe_vs_sector=pe_vs,
                        forward_pe=fundamentals.metrics.forward_pe,
                    )
            except Exception as e:
                logger.warning(f"Valuation comparison error for {ticker}: {e}")
        return None

    async def get_quantitative_report(self, ticker: str) -> QuantitativeReport:
        ticker = ticker.upper().strip()
        fundamentals = await self.get_fundamentals(ticker)
        technicals = await self.get_technical_indicators(ticker)
        valuation = await self.get_valuation_comparison(ticker)
        sources = []
        if fundamentals and not fundamentals.data_unavailable:
            sources.append(fundamentals.source.value)
        if technicals:
            sources.append(technicals.data_source)
        return QuantitativeReport(
            ticker=ticker,
            company_name=fundamentals.company_name if fundamentals else "",
            fundamentals=fundamentals.metrics if fundamentals else None,
            technicals=technicals,
            valuation=valuation,
            data_sources=list(set(sources)),
            retrieved_at=datetime.now(),
        )

    async def get_quantitative_batch(self, tickers: list[str]) -> dict[str, QuantitativeReport]:
        tasks = [self.get_quantitative_report(t) for t in tickers]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        output: dict[str, QuantitativeReport] = {}
        for ticker, result in zip(tickers, results):
            if isinstance(result, Exception):
                output[ticker] = QuantitativeReport(ticker=ticker, data_sources=[])
            else:
                output[ticker] = result
        return output


_service: FundamentalsService | None = None


def get_fundamentals_service() -> FundamentalsService:
    global _service
    if _service is None:
        _service = FundamentalsService()
    return _service
