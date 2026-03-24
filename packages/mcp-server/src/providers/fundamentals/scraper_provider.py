import logging
from models.fundamentals import FundamentalData
from providers.fundamentals.base import FundamentalsProvider

logger = logging.getLogger(__name__)


class ScraperProvider(FundamentalsProvider):
    name = "scraper"
    priority = 3
    timeout = 3.0

    async def get_fundamentals(self, ticker: str) -> FundamentalData | None:
        logger.debug(f"ScraperProvider stub called for {ticker}")
        return None
