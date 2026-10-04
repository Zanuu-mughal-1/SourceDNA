from __future__ import annotations

from pydantic import BaseModel, Field, HttpUrl
from typing import Any


class AnalyzeRequest(BaseModel):
    claim: str = Field(min_length=5, max_length=4000)
    source_urls: list[HttpUrl] = Field(default_factory=list, max_length=30)
    max_sources: int = Field(default=12, ge=3, le=30)


class ExtractClaimsRequest(BaseModel):
    text: str = Field(min_length=20, max_length=20000)
    limit: int = Field(default=5, ge=1, le=10)


class SourceDocument(BaseModel):
    id: str
    url: str
    domain: str
    title: str
    text: str
    published_at: str | None = None
    links: list[str] = Field(default_factory=list)
    search_rank: int | None = None
    snippet: str | None = None


class GraphNode(BaseModel):
    id: str
    label: str
    url: str
    domain: str
    title: str
    cluster: int
    root: bool = False
    primary_candidate: bool = False
    published_at: str | None = None
    claim_snippet: str | None = None


class GraphEdge(BaseModel):
    source: str
    target: str
    kind: str
    weight: float = 1.0
    explanation: str


class AnalysisMetrics(BaseModel):
    cited_urls: int
    unique_domains: int
    independent_roots: int
    derivative_sources: int
    duplicate_pairs: int
    citation_dependencies: int
    evidence_independence_score: int
    claim_drift_score: int
    synthetic_consensus_risk: str


class AnalysisResult(BaseModel):
    claim: str
    metrics: AnalysisMetrics
    verdict: str
    explanation: str
    nodes: list[GraphNode]
    edges: list[GraphEdge]
    root_ids: list[str]
    clusters: dict[str, list[str]]
    warnings: list[str] = Field(default_factory=list)
    methodology: dict[str, Any]
