---
name: evidence-analysis
description: Use SourceDNA when a user wants to know whether multiple citations represent genuinely independent evidence, trace a claim back to likely roots, detect derivative reporting or synthetic consensus, or inspect claim drift.
---

# SourceDNA evidence analysis

Use the SourceDNA MCP tools for evidence-lineage questions.

When the conversation already contains source URLs, pass them to `analyze_evidence` so the analysis is deterministic and does not repeat web discovery. When source URLs are unavailable, call the tool without them only if the deployment has live discovery configured.

Interpret the Evidence Independence Score (EIS) as a source-diversity/provenance heuristic, never as a probability that the claim is true. Clearly distinguish:

- a primary or root candidate,
- derivative or highly similar sources,
- explicit citation dependencies,
- the number of independent evidence roots,
- claim drift,
- and whether the pattern resembles synthetic consensus.

Do not say a claim is true or false solely because its EIS is high or low. A single excellent primary source can be factually correct while scoring lower for independence, and many independent sources can still all be wrong.
