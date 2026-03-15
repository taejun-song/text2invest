import sys
import json
import asyncio
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

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
        report = await pipeline.run(
            selection_text=request.selection_text,
            url=request.url,
            title=request.title,
        )
        return report
    except Exception as e:
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
            report = await pipeline.run(
                selection_text=request.selection_text,
                url=request.url,
                title=request.title,
                on_stage=on_stage,
                on_thinking=on_thinking if request.user_settings.thinking_mode else None,
                on_agent_result=on_agent_result,
            )
            report_json = report.model_dump_json()
            queue.put_nowait(f"event: complete\ndata: {report_json}\n\n")
        except Exception as e:
            queue.put_nowait(f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n")
        finally:
            queue.put_nowait(None)

    async def event_generator():
        task = asyncio.create_task(run_pipeline())
        while True:
            msg = await queue.get()
            if msg is None:
                break
            yield msg
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
    if lang and lang != "en" and lang in LANGUAGE_NAMES:
        system_prompt += f"\n\nIMPORTANT: Respond in {LANGUAGE_NAMES[lang]}."
    messages = [{"role": "system", "content": system_prompt}]
    for msg in request.messages[-10:]:
        messages.append({"role": msg.role, "content": msg.content})
    try:
        llm = LLMProvider(request.user_settings)
        kwargs = llm._build_kwargs()
        kwargs["messages"] = messages
        from litellm import acompletion
        response = await acompletion(**kwargs)
        content = response.choices[0].message.content or ""
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

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
