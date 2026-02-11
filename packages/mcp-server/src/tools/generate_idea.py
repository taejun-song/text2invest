from agents.pipeline import Pipeline
from models.idea_report import IdeaReport, IdeaRequest


async def generate_idea_impl(
    request: IdeaRequest,
    active_generations: dict[str, bool],
) -> IdeaReport:
    request_id = str(id(request))
    active_generations[request_id] = True

    def check_cancelled():
        if not active_generations.get(request_id, True):
            raise ValueError("Generation cancelled")

    try:
        pipeline = Pipeline(request.user_settings)

        def on_stage(stage: str):
            check_cancelled()

        report = await pipeline.run(
            selection_text=request.selection_text,
            url=request.url,
            title=request.title,
            on_stage=on_stage,
        )

        return report
    finally:
        active_generations.pop(request_id, None)
