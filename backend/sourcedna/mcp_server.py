from __future__ import annotations

from typing import Any

try:
    from mcp.server import MCPServer
except ImportError:  # Allows REST API/tests to run without MCP installed.
    MCPServer = None  # type: ignore

from .demo import run_demo
from .service import analyze_claim as analyze_claim_service


if MCPServer is not None:
    mcp = MCPServer("SourceDNA")

    @mcp.tool()
    async def analyze_evidence(claim: str, source_urls: list[str] | None = None, max_sources: int = 12) -> dict[str, Any]:
        """Trace a factual claim through web sources and measure how independent the evidence is.

        Provide source_urls when the host already has citations. If omitted, the SourceDNA deployment must have
        TAVILY_API_KEY configured for live source discovery. The score is evidence independence, not truth.
        """
        result = await analyze_claim_service(claim, source_urls or [], max_sources)
        return result.model_dump()

    @mcp.tool()
    def sourcedna_demo() -> dict[str, Any]:
        """Run SourceDNA's deterministic synthetic-consensus demo without web access."""
        return run_demo().model_dump()
else:
    mcp = None
