import sys
import json
import asyncio
import logging
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
logging.basicConfig(level=logging.INFO)

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import uvicorn

from models.idea_report import IdeaReport, IdeaRequest, Evaluation, UserSettings
from agents.pipeline import Pipeline

active_generations: dict[str, bool] = {}
evaluations: dict[str, Evaluation] = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

app = FastAPI(title="Text2Invest API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    return {"status": "healthy", "version": "0.1.0"}

@app.post("/api/v1/ideas")
async def generate_idea(request: IdeaRequest) -> IdeaReport:
    request_id = str(id(request))
    active_generations[request_id] = True

    try:
        pipeline = Pipeline(request.user_settings)
        report = await asyncio.wait_for(
            pipeline.run(
                selection_text=request.selection_text,
                url=request.url,
                title=request.title,
                user_tickers=request.user_tickers,
            ),
            timeout=600,
        )
        return report
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Pipeline timed out after 10 minutes")
    except Exception as e:
        logging.getLogger(__name__).exception("generate_idea failed")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        active_generations.pop(request_id, None)

@app.post("/api/v1/ideas/stream")
async def generate_idea_stream(request: IdeaRequest):
    queue: asyncio.Queue[str | None] = asyncio.Queue()

    def on_stage(stage: str):
        queue.put_nowait(f"event: stage\ndata: {json.dumps({'stage': stage})}\n\n")

    def on_thinking(agent_id: str, phase: str, content: str):
        queue.put_nowait(
            f"event: thinking\ndata: {json.dumps({'agent_id': agent_id, 'phase': phase, 'content': content})}\n\n"
        )

    def on_agent_result(agent_id: str, summary: dict):
        queue.put_nowait(
            f"event: agent_result\ndata: {json.dumps({'agent_id': agent_id, 'summary': summary})}\n\n"
        )

    async def run_pipeline():
        try:
            pipeline = Pipeline(request.user_settings)
            report = await asyncio.wait_for(
                pipeline.run(
                    selection_text=request.selection_text,
                    url=request.url,
                    title=request.title,
                    on_stage=on_stage,
                    on_thinking=on_thinking if request.user_settings.thinking_mode else None,
                    on_agent_result=on_agent_result,
                    user_tickers=request.user_tickers,
                ),
                timeout=600,
            )
            report_json = report.model_dump_json()
            queue.put_nowait(f"event: complete\ndata: {report_json}\n\n")
        except asyncio.TimeoutError:
            queue.put_nowait(f"event: error\ndata: {json.dumps({'error': 'Pipeline timed out after 10 minutes'})}\n\n")
        except Exception as e:
            queue.put_nowait(f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n")
        finally:
            queue.put_nowait(None)

    async def heartbeat():
        while True:
            await asyncio.sleep(15)
            queue.put_nowait(f"event: heartbeat\ndata: {json.dumps({'ts': int(asyncio.get_event_loop().time())})}\n\n")

    async def event_generator():
        task = asyncio.create_task(run_pipeline())
        hb = asyncio.create_task(heartbeat())
        try:
            while True:
                msg = await queue.get()
                if msg is None:
                    break
                yield msg
        finally:
            hb.cancel()
            await task

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )

@app.post("/api/v1/ideas/{idea_id}/cancel")
async def cancel_generation(idea_id: str):
    if idea_id in active_generations:
        active_generations[idea_id] = False
        return {"cancelled": True}
    return {"cancelled": False}

LANGUAGE_NAMES = {
    "en": "English", "ko": "Korean", "ja": "Japanese", "zh": "Chinese",
    "es": "Spanish", "fr": "French", "de": "German", "pt": "Portuguese",
    "hi": "Hindi", "ar": "Arabic",
}

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    report_context: dict
    messages: list[ChatMessage]
    user_settings: UserSettings

@app.post("/api/v1/chat")
async def chat_with_report(request: ChatRequest):
    from datetime import datetime
    from providers.llm import LLMProvider
    ctx = request.report_context
    tickers = ", ".join(t.get("symbol", "") for t in ctx.get("tickers", []))
    summary_parts = [
        f"Tickers: {tickers}" if tickers else "",
        f"Thesis: {ctx.get('thesis', 'N/A')}",
        f"Executive Summary: {'; '.join(ctx.get('executive_summary', []))}",
        f"Risks: {'; '.join(ctx.get('risks', []))}",
        f"Counter-thesis: {ctx.get('counter_thesis', 'N/A')}",
        f"Confidence: {ctx.get('confidence_score', 'N/A')} — {ctx.get('confidence_explanation', '')}",
        f"Catalysts: {'; '.join(ctx.get('catalysts', []))}",
        f"Limitations: {'; '.join(ctx.get('limitations', []))}",
    ]
    if ctx.get("news_context"):
        summary_parts.append(f"News: {ctx['news_context']}")
    if ctx.get("fundamentals_summary"):
        summary_parts.append(f"Fundamentals: {ctx['fundamentals_summary']}")
    if ctx.get("macro_context"):
        summary_parts.append(f"Macro: {ctx['macro_context']}")
    report_summary = "\n".join(p for p in summary_parts if p)[:4000]
    system_prompt = f"You are an investment analysis assistant. Answer questions about this report:\n\n{report_summary}"
    lang = getattr(request.user_settings, "output_language", None)
    if lang in ("auto", "en", None, ""):
        lang = None
    if lang and lang in LANGUAGE_NAMES:
        system_prompt += f"\n\nIMPORTANT: Respond in {LANGUAGE_NAMES[lang]}."
    messages = [{"role": "system", "content": system_prompt}]
    for msg in request.messages[-10:]:
        messages.append({"role": msg.role, "content": msg.content})
    if lang and lang in LANGUAGE_NAMES:
        messages.append({"role": "system", "content": f"REMINDER: You MUST respond in {LANGUAGE_NAMES[lang]}."})
    try:
        llm = LLMProvider(request.user_settings)
        kwargs = llm._build_kwargs()
        kwargs["messages"] = messages
        from litellm import acompletion
        response = await acompletion(**kwargs)
        msg = response.choices[0].message
        content = msg.content or getattr(msg, "reasoning", None) or getattr(msg, "reasoning_content", None) or ""
        content = LLMProvider._strip_response(content)
        return {"role": "assistant", "content": content, "timestamp": datetime.now().isoformat()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class EvaluationRequest(BaseModel):
    idea_id: str
    rating: str
    notes: str | None = None

@app.post("/api/v1/evaluation")
async def submit_evaluation(req: EvaluationRequest):
    from datetime import datetime
    from uuid import UUID
    evaluation = Evaluation(
        idea_id=UUID(req.idea_id),
        rating=req.rating,
        notes=req.notes,
        created_at=datetime.now(),
    )
    evaluations[req.idea_id] = evaluation
    return evaluation

class TickerSearchRequest(BaseModel):
    query: str
    market_hint: str | None = None

class TickerSearchResult(BaseModel):
    symbol: str
    name: str
    exchange: str

@app.post("/api/v1/tickers/search")
async def search_tickers(req: TickerSearchRequest) -> list[TickerSearchResult]:
    from tools.ticker_search import search_ticker
    matches = search_ticker(req.query, req.market_hint)
    return [TickerSearchResult(symbol=m.symbol, name=m.name, exchange=m.exchange) for m in matches[:5]]

class FundamentalsResponse(BaseModel):
    ticker: str
    company_name: str
    exchange: str
    currency: str
    metrics: dict
    source: str
    retrieved_at: str
    data_unavailable: bool = False
    error_message: str | None = None

class FundamentalsBatchRequest(BaseModel):
    tickers: list[str]

class FundamentalsResponseWithCache(FundamentalsResponse):
    cached: bool = False
    cache_expires_at: str | None = None

@app.get("/api/v1/fundamentals/{ticker}")
async def get_fundamentals(ticker: str, refresh: bool = False) -> FundamentalsResponseWithCache:
    from providers.fundamentals.service import get_fundamentals_service
    service = get_fundamentals_service()
    data = await service.get_fundamentals(ticker, refresh=refresh)
    cache_info = await service.get_cache_info(ticker)
    return FundamentalsResponseWithCache(
        ticker=data.ticker,
        company_name=data.company_name,
        exchange=data.exchange,
        currency=data.currency,
        metrics=data.metrics.model_dump(),
        source=data.source.value,
        retrieved_at=data.retrieved_at.isoformat(),
        data_unavailable=data.data_unavailable,
        error_message=data.error_message,
        cached=cache_info.get("cached", False) if cache_info else False,
        cache_expires_at=cache_info.get("expires_at") if cache_info else None,
    )

@app.post("/api/v1/fundamentals/batch")
async def get_fundamentals_batch(req: FundamentalsBatchRequest, refresh: bool = False) -> dict[str, FundamentalsResponse]:
    from providers.fundamentals.service import get_fundamentals_service
    service = get_fundamentals_service()
    data = await service.get_fundamentals_batch(req.tickers, refresh=refresh)
    return {
        ticker: FundamentalsResponse(
            ticker=d.ticker,
            company_name=d.company_name,
            exchange=d.exchange,
            currency=d.currency,
            metrics=d.metrics.model_dump(),
            source=d.source.value,
            retrieved_at=d.retrieved_at.isoformat(),
            data_unavailable=d.data_unavailable,
            error_message=d.error_message,
        )
        for ticker, d in data.items()
    }

@app.delete("/api/v1/fundamentals/cache")
async def clear_fundamentals_cache():
    from providers.fundamentals.service import get_fundamentals_service
    service = get_fundamentals_service()
    await service.clear_cache()
    return {"cleared": True}

class HistoricalMetricResponse(BaseModel):
    period: str
    period_date: str
    value: float

class HistoricalTrendResponse(BaseModel):
    metric_name: str
    data_points: list[HistoricalMetricResponse]

@app.get("/api/v1/fundamentals/{ticker}/history")
async def get_fundamentals_history(ticker: str, periods: int = 4) -> list[HistoricalTrendResponse]:
    from providers.fundamentals.service import get_fundamentals_service
    service = get_fundamentals_service()
    trends = await service.get_historical(ticker, periods)
    return [
        HistoricalTrendResponse(
            metric_name=t.metric_name,
            data_points=[
                HistoricalMetricResponse(
                    period=p.period,
                    period_date=p.period_date.isoformat(),
                    value=p.value,
                )
                for p in t.data_points
            ],
        )
        for t in trends
    ]

class TechnicalIndicatorsResponse(BaseModel):
    ticker: str
    current_price: float | None = None
    ma_50: float | None = None
    ma_200: float | None = None
    rsi_14: float | None = None
    price_change_1w: float | None = None
    price_change_1m: float | None = None
    price_change_3m: float | None = None
    price_change_ytd: float | None = None
    volume_avg_10d: int | None = None
    retrieved_at: str
    data_source: str = "yfinance"

@app.get("/api/v1/technicals/{ticker}")
async def get_technicals(ticker: str, refresh: bool = False) -> TechnicalIndicatorsResponse:
    from providers.fundamentals.service import get_fundamentals_service
    service = get_fundamentals_service()
    data = await service.get_technical_indicators(ticker, refresh=refresh)
    if not data:
        raise HTTPException(status_code=404, detail=f"Technical indicators not available for {ticker}")
    return TechnicalIndicatorsResponse(
        ticker=data.ticker,
        current_price=data.current_price,
        ma_50=data.ma_50,
        ma_200=data.ma_200,
        rsi_14=data.rsi_14,
        price_change_1w=data.price_change_1w,
        price_change_1m=data.price_change_1m,
        price_change_3m=data.price_change_3m,
        price_change_ytd=data.price_change_ytd,
        volume_avg_10d=data.volume_avg_10d,
        retrieved_at=data.retrieved_at.isoformat(),
        data_source=data.data_source,
    )

class ValuationComparisonResponse(BaseModel):
    ticker: str
    sector: str = ""
    pe_ratio: float | None = None
    sector_pe_avg: float | None = None
    pe_vs_sector: str | None = None
    forward_pe: float | None = None

class QuantitativeReportResponse(BaseModel):
    ticker: str
    company_name: str = ""
    fundamentals: dict | None = None
    technicals: TechnicalIndicatorsResponse | None = None
    valuation: ValuationComparisonResponse | None = None
    data_sources: list[str] = []
    retrieved_at: str

@app.get("/api/v1/quantitative/{ticker}")
async def get_quantitative(ticker: str) -> QuantitativeReportResponse:
    from providers.fundamentals.service import get_fundamentals_service
    service = get_fundamentals_service()
    report = await service.get_quantitative_report(ticker)
    technicals_resp = None
    if report.technicals:
        technicals_resp = TechnicalIndicatorsResponse(
            ticker=report.technicals.ticker,
            current_price=report.technicals.current_price,
            ma_50=report.technicals.ma_50,
            ma_200=report.technicals.ma_200,
            rsi_14=report.technicals.rsi_14,
            price_change_1w=report.technicals.price_change_1w,
            price_change_1m=report.technicals.price_change_1m,
            price_change_3m=report.technicals.price_change_3m,
            price_change_ytd=report.technicals.price_change_ytd,
            volume_avg_10d=report.technicals.volume_avg_10d,
            retrieved_at=report.technicals.retrieved_at.isoformat(),
            data_source=report.technicals.data_source,
        )
    valuation_resp = None
    if report.valuation:
        valuation_resp = ValuationComparisonResponse(
            ticker=report.valuation.ticker,
            sector=report.valuation.sector,
            pe_ratio=report.valuation.pe_ratio,
            sector_pe_avg=report.valuation.sector_pe_avg,
            pe_vs_sector=report.valuation.pe_vs_sector,
            forward_pe=report.valuation.forward_pe,
        )
    return QuantitativeReportResponse(
        ticker=report.ticker,
        company_name=report.company_name,
        fundamentals=report.fundamentals.model_dump() if report.fundamentals else None,
        technicals=technicals_resp,
        valuation=valuation_resp,
        data_sources=report.data_sources,
        retrieved_at=report.retrieved_at.isoformat(),
    )

class QuantitativeBatchRequest(BaseModel):
    tickers: list[str]

@app.post("/api/v1/quantitative/batch")
async def get_quantitative_batch(req: QuantitativeBatchRequest) -> dict[str, QuantitativeReportResponse]:
    from providers.fundamentals.service import get_fundamentals_service
    service = get_fundamentals_service()
    reports = await service.get_quantitative_batch(req.tickers)
    result = {}
    for ticker, report in reports.items():
        technicals_resp = None
        if report.technicals:
            technicals_resp = TechnicalIndicatorsResponse(
                ticker=report.technicals.ticker,
                current_price=report.technicals.current_price,
                ma_50=report.technicals.ma_50,
                ma_200=report.technicals.ma_200,
                rsi_14=report.technicals.rsi_14,
                price_change_1w=report.technicals.price_change_1w,
                price_change_1m=report.technicals.price_change_1m,
                price_change_3m=report.technicals.price_change_3m,
                price_change_ytd=report.technicals.price_change_ytd,
                volume_avg_10d=report.technicals.volume_avg_10d,
                retrieved_at=report.technicals.retrieved_at.isoformat(),
                data_source=report.technicals.data_source,
            )
        valuation_resp = None
        if report.valuation:
            valuation_resp = ValuationComparisonResponse(
                ticker=report.valuation.ticker,
                sector=report.valuation.sector,
                pe_ratio=report.valuation.pe_ratio,
                sector_pe_avg=report.valuation.sector_pe_avg,
                pe_vs_sector=report.valuation.pe_vs_sector,
                forward_pe=report.valuation.forward_pe,
            )
        result[ticker] = QuantitativeReportResponse(
            ticker=report.ticker,
            company_name=report.company_name,
            fundamentals=report.fundamentals.model_dump() if report.fundamentals else None,
            technicals=technicals_resp,
            valuation=valuation_resp,
            data_sources=report.data_sources,
            retrieved_at=report.retrieved_at.isoformat(),
        )
    return result

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
