import asyncio
import logging
from datetime import datetime
from models.fundamentals import DataSourceType, FundamentalData, FundamentalMetrics
from providers.fundamentals.base import FundamentalsProvider

logger = logging.getLogger(__name__)
_last_request_time: float = 0
_request_interval: float = 10.0

MARKET_TO_COUNTRY = {
    "": "united states",
    "KS": "south korea",
    "T": "japan",
    "HK": "hong kong",
    "L": "united kingdom",
    "DE": "germany",
    "PA": "france",
    "MI": "italy",
    "MC": "spain",
    "AS": "netherlands",
}


class InvestpyProvider(FundamentalsProvider):
    name = "investpy"
    priority = 2
    timeout = 5.0

    def _get_country(self, ticker: str) -> str:
        suffix = ticker.split(".")[-1] if "." in ticker else ""
        return MARKET_TO_COUNTRY.get(suffix, "united states")

    async def get_fundamentals(self, ticker: str) -> FundamentalData | None:
        global _last_request_time
        now = asyncio.get_event_loop().time()
        if now - _last_request_time < _request_interval:
            wait_time = _request_interval - (now - _last_request_time)
            logger.debug(f"Investpy rate limit: waiting {wait_time:.1f}s")
            await asyncio.sleep(wait_time)
        _last_request_time = asyncio.get_event_loop().time()
        try:
            import investpy
            symbol = ticker.split(".")[0] if "." in ticker else ticker
            country = self._get_country(ticker)
            try:
                info = investpy.get_stock_information(symbol.lower(), country)
            except Exception:
                return None
            if info is None or info.empty:
                return None
            def safe_get(key: str):
                try:
                    val = info.loc[key].iloc[0] if key in info.index else None
                    if val is not None and str(val).strip() in ("-", "", "N/A"):
                        return None
                    return val
                except Exception:
                    return None
            pe = safe_get("P/E Ratio")
            eps = safe_get("EPS")
            dividend_yield = safe_get("Dividend Yield")
            if dividend_yield:
                try:
                    dividend_yield = float(str(dividend_yield).replace("%", "")) / 100
                except Exception:
                    dividend_yield = None
            metrics = FundamentalMetrics(
                pe_ratio=float(pe) if pe else None,
                eps=float(eps) if eps else None,
                dividend_yield=dividend_yield,
            )
            return FundamentalData(
                ticker=ticker.upper(),
                company_name=safe_get("Prev. Close") or "",
                exchange="",
                currency="USD",
                metrics=metrics,
                source=DataSourceType.INVESTPY,
                retrieved_at=datetime.now(),
            )
        except Exception as e:
            logger.warning(f"Investpy failed for {ticker}: {e}")
            return None
