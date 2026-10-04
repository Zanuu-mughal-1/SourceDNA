from __future__ import annotations

from contextlib import asynccontextmanager
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .claims import extract_candidate_claims
from .demo import run_demo
from .models import AnalyzeRequest, ExtractClaimsRequest
from .search import SearchNotConfigured
from .service import analyze_claim
from .mcp_server import mcp

mcp_app = None
if mcp is not None:
    mcp_app = mcp.streamable_http_app(
        streamable_http_path="/mcp",
        json_response=True,
        stateless_http=True,
        host=os.getenv("MCP_HOST", "0.0.0.0"),
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    if mcp is not None and mcp_app is not None:
        async with mcp.session_manager.run():
            yield
    else:
        yield


app = FastAPI(
    title="SourceDNA API",
    version="0.1.0",
    description="Trace source lineage, derivative evidence and synthetic consensus. EIS measures independence, not truth.",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[x.strip() for x in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",") if x.strip()],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"ok": True, "service": "SourceDNA", "version": "0.1.0", "mcp": mcp is not None}


@app.get("/api/demo")
def demo():
    return run_demo()


@app.post("/api/extract-claims")
def extract_claims(req: ExtractClaimsRequest):
    return {"claims": extract_candidate_claims(req.text, req.limit)}


@app.post("/api/analyze")
async def analyze(req: AnalyzeRequest):
    try:
        return await analyze_claim(req.claim, [str(u) for u in req.source_urls], req.max_sources)
    except SearchNotConfigured as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Analysis failed: {type(exc).__name__}: {exc}") from exc


if mcp_app is not None:
    # Merge MCP routes into the main ASGI app so the public endpoint is exactly /mcp.
    # The top-level lifespan above owns the MCP session manager.
    app.routes.extend(mcp_app.routes)

# Production Docker builds the frontend first and places it here.
frontend_dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if frontend_dist.exists():
    assets = frontend_dist / "assets"
    if assets.exists():
        app.mount("/assets", StaticFiles(directory=str(assets)), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def spa(full_path: str):
        target = frontend_dist / full_path
        if full_path and target.exists() and target.is_file():
            return FileResponse(target)
        return FileResponse(frontend_dist / "index.html")
