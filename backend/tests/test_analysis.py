from sourcedna.demo import run_demo
from sourcedna.claims import extract_candidate_claims


def test_demo_detects_synthetic_consensus():
    r = run_demo()
    assert r.metrics.cited_urls == 6
    assert 1 <= r.metrics.independent_roots < r.metrics.cited_urls
    assert r.metrics.evidence_independence_score < 70
    assert r.metrics.synthetic_consensus_risk in {"medium", "high"}
    assert len(r.nodes) == 6


def test_claim_extraction_prefers_specific_claims():
    text = "Welcome to the report. A 2026 survey found that 61% of teams use AI every day. The rest of this paragraph is commentary."
    claims = extract_candidate_claims(text, 3)
    assert claims
    assert "61%" in claims[0]
