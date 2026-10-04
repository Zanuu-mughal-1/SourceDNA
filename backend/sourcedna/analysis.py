from __future__ import annotations

from collections import defaultdict
from datetime import datetime
import math
import re
from urllib.parse import urlparse

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .models import AnalysisMetrics, AnalysisResult, GraphEdge, GraphNode, SourceDocument
from .utils import clean_text, normalize_url

SIMILARITY_THRESHOLD = 0.62
CITATION_SIM_THRESHOLD = 0.18


class UnionFind:
    def __init__(self, ids: list[str]):
        self.p = {x: x for x in ids}
    def find(self, x: str) -> str:
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x
    def union(self, a: str, b: str) -> None:
        a, b = self.find(a), self.find(b)
        if a != b:
            self.p[b] = a


def _date_key(value: str | None) -> tuple[int, str]:
    if not value:
        return (1, "9999")
    try:
        return (0, datetime.fromisoformat(value.replace("Z", "+00:00")).isoformat())
    except ValueError:
        return (0, value)


def _article_similarity(docs: list[SourceDocument]) -> np.ndarray:
    if len(docs) <= 1:
        return np.eye(len(docs))
    corpus = [d.text[:50_000] for d in docs]
    vec = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), max_features=12000, min_df=1)
    x = vec.fit_transform(corpus)
    return cosine_similarity(x)


def _claim_snippets(claim: str, docs: list[SourceDocument]) -> dict[str, str]:
    sentences_by_doc: list[list[str]] = []
    flat: list[str] = [claim]
    refs: list[tuple[str, int]] = []
    for d in docs:
        sents = [clean_text(s) for s in re.split(r"(?<=[.!?])\s+", d.text) if 30 <= len(clean_text(s)) <= 550][:300]
        sentences_by_doc.append(sents)
        for i, s in enumerate(sents):
            flat.append(s)
            refs.append((d.id, i))
    if len(flat) == 1:
        return {d.id: "" for d in docs}
    try:
        v = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), max_features=10000)
        x = v.fit_transform(flat)
        sims = cosine_similarity(x[0:1], x[1:]).ravel()
    except ValueError:
        return {d.id: (d.text[:300] + "…") for d in docs}
    best: dict[str, tuple[float, str]] = {d.id: (-1, "") for d in docs}
    for score, (did, idx) in zip(sims, refs):
        s = sentences_by_doc[[d.id for d in docs].index(did)][idx]
        if score > best[did][0]:
            best[did] = (float(score), s)
    return {k: v[1] for k, v in best.items()}


def _snippet_drift(snippets: dict[str, str], roots: list[str]) -> int:
    texts = [t for t in snippets.values() if t]
    if len(texts) < 2:
        return 0
    try:
        v = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
        x = v.fit_transform(texts)
        sim = cosine_similarity(x)
        upper = sim[np.triu_indices_from(sim, k=1)]
        mean_sim = float(np.mean(upper)) if len(upper) else 1.0
        return int(round(max(0, min(1, 1 - mean_sim)) * 100))
    except ValueError:
        return 0


def analyze_documents(claim: str, docs: list[SourceDocument], inherited_warnings: list[str] | None = None) -> AnalysisResult:
    warnings = list(inherited_warnings or [])
    if len(docs) < 2:
        raise ValueError("At least two readable sources are required for lineage analysis.")

    # De-duplicate exact normalized URLs before scoring.
    uniq: dict[str, SourceDocument] = {}
    for d in docs:
        uniq.setdefault(normalize_url(d.url), d)
    docs = list(uniq.values())
    if len(docs) < 2:
        raise ValueError("At least two unique readable sources are required.")

    ids = [d.id for d in docs]
    by_id = {d.id: d for d in docs}
    sim = _article_similarity(docs)
    snippets = _claim_snippets(claim, docs)
    uf = UnionFind(ids)
    duplicate_pairs = 0

    edges: list[GraphEdge] = []
    for i in range(len(docs)):
        for j in range(i + 1, len(docs)):
            s = float(sim[i, j])
            if s >= SIMILARITY_THRESHOLD:
                duplicate_pairs += 1
                uf.union(docs[i].id, docs[j].id)

    raw_clusters: dict[str, list[str]] = defaultdict(list)
    for did in ids:
        raw_clusters[uf.find(did)].append(did)

    # Stable numeric cluster labels.
    cluster_groups = list(raw_clusters.values())
    cluster_groups.sort(key=lambda group: min(_date_key(by_id[x].published_at) for x in group))
    cluster_of: dict[str, int] = {}
    cluster_root: dict[int, str] = {}
    for cidx, group in enumerate(cluster_groups):
        for did in group:
            cluster_of[did] = cidx
        root = min(group, key=lambda x: (_date_key(by_id[x].published_at), by_id[x].search_rank or 999, by_id[x].url))
        cluster_root[cidx] = root
        for did in group:
            if did == root:
                continue
            weight = float(sim[ids.index(did), ids.index(root)])
            edges.append(GraphEdge(
                source=did,
                target=root,
                kind="derivative",
                weight=round(weight, 3),
                explanation=f"High article-text similarity ({weight:.0%}) suggests this source may be derivative of the cluster root.",
            ))

    # Detect explicit links between analyzed sources. An article linking to another source is dependent evidence,
    # but we keep it separate from text-derivative clustering.
    normalized_to_id = {normalize_url(d.url): d.id for d in docs}
    citation_dependencies = 0
    cluster_depends_on: dict[int, set[int]] = defaultdict(set)
    existing_pairs = {(e.source, e.target, e.kind) for e in edges}
    for d in docs:
        for link in d.links:
            target = normalized_to_id.get(normalize_url(link))
            if not target or target == d.id:
                continue
            source_c, target_c = cluster_of[d.id], cluster_of[target]
            if source_c != target_c:
                citation_dependencies += 1
                cluster_depends_on[source_c].add(target_c)
            key = (d.id, target, "citation")
            if key not in existing_pairs:
                edges.append(GraphEdge(
                    source=d.id,
                    target=target,
                    kind="citation",
                    weight=1.0,
                    explanation="The source explicitly links to another analyzed source, so the two pieces of evidence are not fully independent.",
                ))
                existing_pairs.add(key)

    # Independent roots are lineage clusters that do not explicitly depend on another analyzed cluster.
    independent_cluster_ids = [i for i in range(len(cluster_groups)) if not cluster_depends_on.get(i)]
    root_ids = [cluster_root[i] for i in independent_cluster_ids]
    if not root_ids:
        # Cycles can happen; retain earliest root candidate so the score remains interpretable.
        earliest_cluster = min(range(len(cluster_groups)), key=lambda c: _date_key(by_id[cluster_root[c]].published_at))
        root_ids = [cluster_root[earliest_cluster]]
        warnings.append("A citation cycle was detected; the earliest cluster root is shown as the fallback evidence root.")

    domains = {d.domain for d in docs}
    n = len(docs)
    roots_n = len(root_ids)
    derivative_sources = n - roots_n
    independence_ratio = roots_n / n
    root_count_factor = min(1.0, roots_n / 3.0)
    domain_diversity = len(domains) / n
    pair_count = max(1, n * (n - 1) / 2)
    duplicate_rate = duplicate_pairs / pair_count
    drift = _snippet_drift(snippets, root_ids)

    score = 100 * (
        0.48 * independence_ratio
        + 0.25 * root_count_factor
        + 0.17 * domain_diversity
        + 0.10 * (1 - drift / 100)
    ) - 20 * duplicate_rate
    eis = int(round(max(0, min(100, score))))

    consensus_ratio = roots_n / n
    if n >= 4 and consensus_ratio <= 0.25:
        risk = "high"
    elif n >= 4 and consensus_ratio <= 0.5:
        risk = "medium"
    else:
        risk = "low"

    if eis >= 75:
        verdict = "Multiple genuinely independent evidence chains were found."
    elif eis >= 50:
        verdict = "The evidence is mixed: several sources appear dependent or derivative."
    elif eis >= 25:
        verdict = "Apparent consensus is much stronger than the underlying source independence."
    else:
        verdict = "Strong synthetic-consensus risk: most sources collapse to very few evidence roots."

    nodes: list[GraphNode] = []
    for d in docs:
        root = d.id in root_ids
        nodes.append(GraphNode(
            id=d.id,
            label=(d.title[:52] + "…") if len(d.title) > 52 else d.title,
            url=d.url,
            domain=d.domain,
            title=d.title,
            cluster=cluster_of[d.id],
            root=root,
            primary_candidate=root,
            published_at=d.published_at,
            claim_snippet=snippets.get(d.id) or None,
        ))

    clusters = {str(i): group for i, group in enumerate(cluster_groups)}
    metrics = AnalysisMetrics(
        cited_urls=n,
        unique_domains=len(domains),
        independent_roots=roots_n,
        derivative_sources=derivative_sources,
        duplicate_pairs=duplicate_pairs,
        citation_dependencies=citation_dependencies,
        evidence_independence_score=eis,
        claim_drift_score=drift,
        synthetic_consensus_risk=risk,
    )
    return AnalysisResult(
        claim=claim,
        metrics=metrics,
        verdict=verdict,
        explanation=(
            f"SourceDNA found {n} readable sources across {len(domains)} domains, but only {roots_n} "
            f"independent evidence root{'s' if roots_n != 1 else ''}. The EIS measures source independence, not factual truth."
        ),
        nodes=nodes,
        edges=edges,
        root_ids=root_ids,
        clusters=clusters,
        warnings=warnings,
        methodology={
            "article_similarity": "TF-IDF cosine similarity over article text",
            "derivative_threshold": SIMILARITY_THRESHOLD,
            "root_logic": "Earliest/rank-prioritized source per derivative cluster, adjusted for explicit cross-source links",
            "claim_drift": "Average divergence among the sentences most relevant to the claim",
            "score_note": "Experimental heuristic. It is an evidence-independence signal, not a truth probability.",
        },
    )
