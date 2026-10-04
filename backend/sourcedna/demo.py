from __future__ import annotations

from .analysis import analyze_documents
from .models import SourceDocument

DEMO_CLAIM = "People who study after 11 PM retain 37% more information."

COMMON = (
    "The discussion concerns study timing, memory retention, late-night learning, student productivity and revision habits. "
    "The pages repeat the same survey framing, refer to the same group of respondents and use the same late-night versus daytime comparison. "
    "They do not identify a randomized controlled experiment, peer-reviewed memory test or independent replication. "
    "The statistic spread quickly through study-advice websites after the original productivity post appeared online. "
)


def demo_documents() -> list[SourceDocument]:
    variants = [
        (
            "s_root", "study-spark.example", "Our Late-Night Study Poll",
            "An informal poll of 42 followers claimed that people who study after 11 PM retain 37% more information. "
            "No controlled memory test was performed and no academic paper was cited.",
            "2026-09-01T09:00:00+00:00", []
        ),
        (
            "s_copy1", "learning-daily.example", "Late Night Learners Remember 37% More",
            "A student productivity survey reported that learners studying after 11 PM retain 37% more information. "
            "The result was presented as a possible advantage for night-time learners.",
            "2026-09-03T10:00:00+00:00", ["https://study-spark.example/original-poll"]
        ),
        (
            "s_copy2", "campus-focus.example", "Why 11 PM May Be the Best Time to Study",
            "Students remember 37 percent more information when they study after 11 PM, according to a productivity survey repeated online. "
            "The article describes the result as a late-night learning advantage.",
            "2026-09-04T10:00:00+00:00", ["https://study-spark.example/original-poll"]
        ),
        (
            "s_copy3", "brain-hacks.example", "Late Study Can Boost Retention",
            "Studying after 11 PM improves memory retention by 37%, a finding now circulating across education websites. "
            "The post turns the original survey result into a general recommendation for students.",
            "2026-09-05T10:00:00+00:00", ["https://learning-daily.example/night-study"]
        ),
        (
            "s_copy4", "student-wire.example", "Science Says Night Owls Learn Better",
            "Late-night students may learn roughly 37% better after 11 PM. The statistic is described as evidence that night owls have a biological learning advantage. "
            "The wording is stronger than the original informal survey.",
            "2026-09-06T10:00:00+00:00", ["https://brain-hacks.example/night-study"]
        ),
        (
            "s_copy5", "future-learning.example", "The 11 PM Memory Rule",
            "Studying after 11 PM can make your brain retain around 37% more information, according to reports shared across student sites. "
            "The page presents the number as an established memory rule despite tracing back to the same online poll.",
            "2026-09-07T10:00:00+00:00", ["https://student-wire.example/night-study"]
        ),
    ]
    docs: list[SourceDocument] = []
    for rank, (sid, domain, title, claim_text, date, links) in enumerate(variants, start=1):
        path = "original-poll" if sid == "s_root" else "night-study"
        docs.append(SourceDocument(
            id=sid,
            url=f"https://{domain}/{path}",
            domain=domain,
            title=title,
            text=claim_text + " " + COMMON,
            published_at=date,
            links=links,
            search_rank=rank,
        ))
    return docs


def run_demo():
    return analyze_documents(DEMO_CLAIM, demo_documents(), [
        "Demo mode uses synthetic local webpages so it works without internet access or API keys."
    ])
