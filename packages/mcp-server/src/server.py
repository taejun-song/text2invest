import sys
from datetime import datetime
from pathlib import Path
from uuid import UUID

sys.path.insert(0, str(Path(__file__).parent))

from fastmcp import FastMCP

from models import Evaluation, IdeaReport, IdeaRequest

mcp = FastMCP("Text2Invest MCP Server")

VERSION = "0.1.0"
evaluations: dict[str, Evaluation] = {}
active_generations: dict[str, bool] = {}


@mcp.tool()
async def health() -> dict:
    return {"status": "healthy", "version": VERSION}


@mcp.tool()
async def generate_idea(request: IdeaRequest) -> IdeaReport:
    from tools.generate_idea import generate_idea_impl

    return await generate_idea_impl(request, active_generations)


@mcp.tool()
async def cancel_generation(idea_id: str) -> dict:
    if idea_id in active_generations:
        active_generations[idea_id] = False
        return {"cancelled": True}
    return {"cancelled": False}


@mcp.tool()
async def submit_evaluation(idea_id: str, rating: str, notes: str | None = None) -> Evaluation:
    evaluation = Evaluation(
        idea_id=UUID(idea_id),
        rating=rating,  # type: ignore
        notes=notes,
        created_at=datetime.now(),
    )
    evaluations[idea_id] = evaluation
    return evaluation


def main():
    mcp.run()


if __name__ == "__main__":
    main()
