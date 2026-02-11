import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
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

@app.post("/api/v1/ideas/{idea_id}/cancel")
async def cancel_generation(idea_id: str):
    if idea_id in active_generations:
        active_generations[idea_id] = False
        return {"cancelled": True}
    return {"cancelled": False}

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
