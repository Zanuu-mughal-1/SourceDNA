from __future__ import annotations

import re
from .utils import clean_text

_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9])")


def extract_candidate_claims(text: str, limit: int = 5) -> list[str]:
    text = clean_text(text)
    sentences = _SENTENCE_RE.split(text)
    scored: list[tuple[float, str]] = []
    for sentence in sentences:
        s = sentence.strip(" -•\t")
        if len(s) < 35 or len(s) > 420:
            continue
        score = 0.0
        if re.search(r"\b\d+(?:\.\d+)?%?\b", s):
            score += 3
        if re.search(r"\b(study|research|report|found|shows|suggests|increased|decreased|causes|reduces|improves|will|is|are)\b", s, re.I):
            score += 2
        if re.search(r"\b(according to|evidence|data|scientists|researchers|experts)\b", s, re.I):
            score += 1
        score += min(len(s) / 200, 1)
        scored.append((score, s))
    scored.sort(key=lambda x: (-x[0], len(x[1])))
    out: list[str] = []
    for _, s in scored:
        if s not in out:
            out.append(s)
        if len(out) >= limit:
            break
    return out or ([text[:420]] if text else [])
