import asyncio
import sys
import json
sys.path.insert(0, "packages/mcp-server/src")

from models.idea_report import UserSettings, Provider
from agents.pipeline import Pipeline

TEST_TEXT = """
Apple Inc. reported record quarterly revenue of $119.6 billion, up 4% year over year,
driven by strong iPhone sales and services growth. CEO Tim Cook highlighted the company's
continued investment in AI and machine learning capabilities. The company also announced
a $110 billion stock buyback program, the largest in US history. Analysts expect
continued growth in the services segment, which now represents over 20% of total revenue.
"""

async def main():
    settings = UserSettings(
        provider=Provider.OPENAI,
        model="Qwen/Qwen2.5-32B-Instruct-AWQ",
        api_key="not-needed",
        base_url="https://morales.tail784d0.ts.net/v1",
        temperature=0.7,
        pii_redaction=True,
        web_lookup=False,
    )

    pipeline = Pipeline(settings)

    print("Starting pipeline...")
    print("-" * 50)

    def on_stage(stage: str):
        print(f"Stage: {stage}")

    report = await pipeline.run(
        selection_text=TEST_TEXT,
        url="https://example.com/apple-earnings",
        title="Apple Q4 Earnings Report",
        on_stage=on_stage,
    )

    print("-" * 50)
    print("Report generated!")
    print(f"Tickers: {[t.symbol for t in report.tickers]}")
    print(f"Thesis: {report.thesis[:200]}...")
    print(f"Confidence: {report.confidence_score:.0%}")
    print(f"Risks: {report.risks}")
    print(f"Duration: {report.provider_meta.pipeline_duration_ms}ms")

if __name__ == "__main__":
    asyncio.run(main())
