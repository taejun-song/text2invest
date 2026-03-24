from abc import ABC, abstractmethod
from models.fundamentals import FundamentalData, HistoricalTrend


class FundamentalsProvider(ABC):
    name: str = "base"
    priority: int = 999
    supported_markets: list[str] = []
    timeout: float = 5.0

    @abstractmethod
    async def get_fundamentals(self, ticker: str) -> FundamentalData | None:
        pass

    async def get_historical(self, ticker: str, periods: int = 4) -> list[HistoricalTrend]:
        return []

    def supports_market(self, ticker: str) -> bool:
        if not self.supported_markets:
            return True
        suffix = ticker.split(".")[-1] if "." in ticker else ""
        return suffix in self.supported_markets or not suffix
