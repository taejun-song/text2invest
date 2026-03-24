import json
import logging
import aiosqlite
from datetime import datetime, timedelta
from pathlib import Path
from models.fundamentals import DataSourceType, FundamentalData, FundamentalMetrics, HistoricalTrend, HistoricalMetric

logger = logging.getLogger(__name__)
DEFAULT_TTL_HOURS = 24
DB_PATH = Path(__file__).parent.parent.parent / "data" / "fundamentals.db"


class FundamentalsCache:
    def __init__(self, db_path: Path | None = None):
        self.db_path = db_path or DB_PATH
        self._initialized = False

    async def _ensure_initialized(self):
        if self._initialized:
            return
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS fundamentals_cache (
                        ticker TEXT PRIMARY KEY,
                        data TEXT NOT NULL,
                        source TEXT NOT NULL,
                        fetched_at TEXT NOT NULL,
                        expires_at TEXT NOT NULL
                    )
                """)
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS historical_metrics (
                        ticker TEXT NOT NULL,
                        metric_name TEXT NOT NULL,
                        data TEXT NOT NULL,
                        fetched_at TEXT NOT NULL,
                        expires_at TEXT NOT NULL,
                        PRIMARY KEY (ticker, metric_name)
                    )
                """)
                await db.commit()
            self._initialized = True
        except Exception as e:
            logger.error(f"Failed to initialize cache: {e}")
            await self._recreate_db()

    async def _recreate_db(self):
        try:
            if self.db_path.exists():
                self.db_path.unlink()
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    CREATE TABLE fundamentals_cache (
                        ticker TEXT PRIMARY KEY,
                        data TEXT NOT NULL,
                        source TEXT NOT NULL,
                        fetched_at TEXT NOT NULL,
                        expires_at TEXT NOT NULL
                    )
                """)
                await db.execute("""
                    CREATE TABLE historical_metrics (
                        ticker TEXT NOT NULL,
                        metric_name TEXT NOT NULL,
                        data TEXT NOT NULL,
                        fetched_at TEXT NOT NULL,
                        expires_at TEXT NOT NULL,
                        PRIMARY KEY (ticker, metric_name)
                    )
                """)
                await db.commit()
            self._initialized = True
            logger.info("Cache database recreated")
        except Exception as e:
            logger.error(f"Failed to recreate cache: {e}")

    async def get_cached(self, ticker: str) -> FundamentalData | None:
        await self._ensure_initialized()
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    "SELECT data, source, fetched_at, expires_at FROM fundamentals_cache WHERE ticker = ?",
                    (ticker.upper(),),
                )
                row = await cursor.fetchone()
                if not row:
                    logger.debug(f"Cache miss for {ticker}")
                    return None
                data_json, source, fetched_at, expires_at = row
                expires = datetime.fromisoformat(expires_at)
                if datetime.now() > expires:
                    logger.debug(f"Cache expired for {ticker}")
                    return None
                logger.debug(f"Cache hit for {ticker}")
                data_dict = json.loads(data_json)
                metrics = FundamentalMetrics(**data_dict.get("metrics", {}))
                return FundamentalData(
                    ticker=data_dict["ticker"],
                    company_name=data_dict.get("company_name", ""),
                    exchange=data_dict.get("exchange", ""),
                    currency=data_dict.get("currency", "USD"),
                    metrics=metrics,
                    source=DataSourceType.CACHE,
                    retrieved_at=datetime.fromisoformat(fetched_at),
                    data_unavailable=data_dict.get("data_unavailable", False),
                    error_message=data_dict.get("error_message"),
                )
        except Exception as e:
            logger.warning(f"Cache read failed for {ticker}: {e}")
            return None

    async def set_cached(self, ticker: str, data: FundamentalData, ttl_hours: int = DEFAULT_TTL_HOURS):
        await self._ensure_initialized()
        try:
            fetched_at = data.retrieved_at.isoformat()
            expires_at = (datetime.now() + timedelta(hours=ttl_hours)).isoformat()
            data_dict = {
                "ticker": data.ticker,
                "company_name": data.company_name,
                "exchange": data.exchange,
                "currency": data.currency,
                "metrics": data.metrics.model_dump(),
                "data_unavailable": data.data_unavailable,
                "error_message": data.error_message,
            }
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    """INSERT OR REPLACE INTO fundamentals_cache (ticker, data, source, fetched_at, expires_at)
                       VALUES (?, ?, ?, ?, ?)""",
                    (ticker.upper(), json.dumps(data_dict), data.source.value, fetched_at, expires_at),
                )
                await db.commit()
            logger.debug(f"Cached fundamentals for {ticker}")
        except Exception as e:
            logger.warning(f"Cache write failed for {ticker}: {e}")

    async def is_expired(self, ticker: str) -> bool:
        await self._ensure_initialized()
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    "SELECT expires_at FROM fundamentals_cache WHERE ticker = ?",
                    (ticker.upper(),),
                )
                row = await cursor.fetchone()
                if not row:
                    return True
                expires = datetime.fromisoformat(row[0])
                return datetime.now() > expires
        except Exception:
            return True

    async def delete_cached(self, ticker: str):
        await self._ensure_initialized()
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("DELETE FROM fundamentals_cache WHERE ticker = ?", (ticker.upper(),))
                await db.commit()
        except Exception as e:
            logger.warning(f"Cache delete failed for {ticker}: {e}")

    async def clear_all(self):
        await self._ensure_initialized()
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("DELETE FROM fundamentals_cache")
                await db.commit()
            logger.info("Cache cleared")
        except Exception as e:
            logger.warning(f"Cache clear failed: {e}")

    async def get_cache_info(self, ticker: str) -> dict | None:
        await self._ensure_initialized()
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    "SELECT source, fetched_at, expires_at FROM fundamentals_cache WHERE ticker = ?",
                    (ticker.upper(),),
                )
                row = await cursor.fetchone()
                if not row:
                    return None
                source, fetched_at, expires_at = row
                return {
                    "cached": True,
                    "source": source,
                    "fetched_at": fetched_at,
                    "expires_at": expires_at,
                }
        except Exception:
            return None

    async def get_historical_cached(self, ticker: str) -> list[HistoricalTrend] | None:
        await self._ensure_initialized()
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    "SELECT metric_name, data, expires_at FROM historical_metrics WHERE ticker = ?",
                    (ticker.upper(),),
                )
                rows = await cursor.fetchall()
                if not rows:
                    return None
                trends = []
                for metric_name, data_json, expires_at in rows:
                    if datetime.now() > datetime.fromisoformat(expires_at):
                        continue
                    data_points = json.loads(data_json)
                    points = [HistoricalMetric(**p) for p in data_points]
                    trends.append(HistoricalTrend(metric_name=metric_name, data_points=points))
                return trends if trends else None
        except Exception as e:
            logger.warning(f"Historical cache read failed for {ticker}: {e}")
            return None

    async def set_historical_cached(self, ticker: str, trends: list[HistoricalTrend], ttl_hours: int = DEFAULT_TTL_HOURS):
        await self._ensure_initialized()
        try:
            fetched_at = datetime.now().isoformat()
            expires_at = (datetime.now() + timedelta(hours=ttl_hours)).isoformat()
            async with aiosqlite.connect(self.db_path) as db:
                for trend in trends:
                    data_points = [{"period": p.period, "period_date": p.period_date.isoformat(), "value": p.value} for p in trend.data_points]
                    await db.execute(
                        """INSERT OR REPLACE INTO historical_metrics (ticker, metric_name, data, fetched_at, expires_at)
                           VALUES (?, ?, ?, ?, ?)""",
                        (ticker.upper(), trend.metric_name, json.dumps(data_points), fetched_at, expires_at),
                    )
                await db.commit()
            logger.debug(f"Cached historical for {ticker}")
        except Exception as e:
            logger.warning(f"Historical cache write failed for {ticker}: {e}")


_cache: FundamentalsCache | None = None


def get_fundamentals_cache() -> FundamentalsCache:
    global _cache
    if _cache is None:
        _cache = FundamentalsCache()
    return _cache
