# SourceDNA 🧬

**The internet counts repetition as evidence. SourceDNA doesn't.**

SourceDNA is a hackathon-ready web app + REST API + MCP server that traces a factual claim through web sources, groups highly derivative reporting, finds likely evidence roots, estimates claim drift, and produces an experimental **Evidence Independence Score (EIS)**.

> SourceDNA does **not** decide whether a claim is true. It measures whether the sources supporting/discussing a claim are genuinely independent or mostly descendants of the same evidence chain.

## What is included

- React 19 + Vite 8 frontend
- FastAPI backend
- Live webpage extraction with SSRF safeguards and size/time limits
- Optional Tavily-powered web discovery
- TF-IDF article similarity and derivative clustering
- Explicit citation/link dependency detection
- Evidence-root estimation
- Claim-relevant sentence extraction and drift estimate
- Interactive lineage graph data and polished dashboard
- Deterministic offline demo for judging/testing
- REST API
- **MCP 2.3 server** for ChatGPT and other MCP hosts
- Agent Plugin package template and builder script
- OpenAPI schema as an optional Custom GPT Actions fallback
- Docker deployment
- Backend tests + GitHub Actions CI

## Architecture

```text
                           ┌──────────────────────┐
Claim / AI answer ────────▶│ SourceDNA frontend   │
                           └─────────┬────────────┘
                                     │ /api/analyze
                                     ▼
                           ┌──────────────────────┐
                           │ FastAPI / MCP server │◀──── ChatGPT / MCP hosts
                           └─────────┬────────────┘
                                     │
                    ┌────────────────┴────────────────┐
                    │                                 │
             supplied URLs                     live discovery
                    │                         (Tavily optional)
                    └────────────────┬────────────────┘
                                     ▼
                          Fetch + parse webpages
                                     ▼
                     TF-IDF similarity + links
                                     ▼
                       Lineage / root analysis
                                     ▼
                EIS + claim drift + graph + verdict
```

## Fastest local test

### 1. Backend

```bash
cd backend
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
# source .venv/bin/activate

pip install -r requirements.txt
uvicorn sourcedna.app:app --reload --port 8000
```

Open `http://localhost:8000/api/health`.

The backend also serves the MCP endpoint at:

```text
http://localhost:8000/mcp
```

### 2. Frontend

In another terminal:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173` and click **Run synthetic-consensus demo**. The demo needs no API key and no internet.

### 3. Run backend tests

```bash
cd backend
pytest -q
```

## Live web discovery

SourceDNA can always analyze URLs you paste into the UI or pass to the API/MCP tool.

For automatic web search, set:

```bash
TAVILY_API_KEY=your_key_here
```

Then restart the backend. Search is intentionally isolated from the scoring engine, so another provider can be added later without changing the EIS logic.

## REST API

### Analyze a claim using known source URLs

```bash
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "claim":"Remote workers are 47% more productive.",
    "source_urls":[
      "https://example.com/article-a",
      "https://example.org/report-b"
    ],
    "max_sources":12
  }'
```

### Analyze with automatic discovery

Omit `source_urls` after setting `TAVILY_API_KEY`.

### Built-in deterministic demo

```bash
curl http://localhost:8000/api/demo
```

## How EIS works in this MVP

The current score is intentionally transparent and heuristic. It combines:

1. **Independent-root ratio** — how many evidence lineages remain after derivative clustering and explicit citation dependencies.
2. **Absolute root count** — multiple independent roots are rewarded, saturating after three.
3. **Domain diversity** — a small additional signal, not treated as proof of independence.
4. **Claim drift** — divergence between the claim-relevant sentence in each source.
5. **Duplicate penalty** — high-similarity article pairs reduce the score.

Derivative clustering currently uses TF-IDF cosine similarity with a default threshold of `0.62`. This is deliberately simple enough to explain to judges. A later version can add embedding models, cross-encoders, citation databases, archive timestamps, C2PA metadata, and LLM-assisted relation classification.

## Use SourceDNA in ChatGPT as a plugin (current 2026 path)

ChatGPT's current plugin architecture uses **MCP**. You do not need the retired old-style `ai-plugin.json` manifest.

### Option A — quickest test: connect the MCP URL directly

1. Deploy SourceDNA somewhere that gives you a public **HTTPS** URL.
2. Confirm these work:
   - `https://YOUR-DOMAIN/api/health`
   - `https://YOUR-DOMAIN/mcp`
3. In ChatGPT, open **Settings → Security and login** and enable **Developer mode**.
4. Open **Plugins**, press the **+** button, and add your MCP server URL:

   ```text
   https://YOUR-DOMAIN/mcp
   ```

5. Name it **SourceDNA**, add a short description, and create it.
6. Start a new chat, select SourceDNA from the plugin/More menu, then try:

   ```text
   Use SourceDNA to analyze whether the sources behind this claim are genuinely independent: "..."
   ```

For development from your own computer, run the server locally and expose port 8000 with an HTTPS tunnel such as ngrok, then give ChatGPT the tunnel URL ending in `/mcp`.

> The OpenAI MCP quickstart says ChatGPT requires a publicly reachable HTTPS MCP endpoint during development. After you change tool metadata/server behavior, refresh the plugin connection in ChatGPT.

### Option B — build the installable Agent Plugin ZIP

After deployment, run:

```bash
python scripts/make_plugin.py --mcp-url https://YOUR-DOMAIN/mcp
```

It creates:

```text
dist/sourcedna-plugin.zip
```

The package contains:

```text
sourcedna/
  plugin.json
  mcp.json
  skills/evidence-analysis/SKILL.md
```

You can use that package with Plugin Creator / your personal plugin workflow. The repository keeps `mcp.json.template` instead of hard-coding a fake server URL.

## Test the MCP server before ChatGPT

The official MCP Inspector is the best protocol-level test:

```bash
npx @modelcontextprotocol/inspector@latest
```

Choose **Streamable HTTP** and connect to:

```text
http://localhost:8000/mcp
```

You should see these SourceDNA tools:

- `analyze_evidence`
- `sourcedna_demo`

Try `sourcedna_demo` first because it requires no network key.

## Deploy from GitHub

### Docker (recommended)

```bash
docker build -t sourcedna .
docker run --rm -p 8000:8000 -e TAVILY_API_KEY=YOUR_KEY sourcedna
```

The single container builds the React frontend and serves it from FastAPI, so one public domain provides:

- `/` — website
- `/api/...` — REST API
- `/mcp` — ChatGPT/MCP endpoint

### Render

A starter `render.yaml` is included. Push this repository to GitHub, create a Render Blueprint/web service from the repository, and add `TAVILY_API_KEY` as a secret environment variable if you want live discovery.

Railway, Fly.io, Azure, GCP, AWS, DigitalOcean or any Docker-capable host can use the same image.

## GitHub upload

```bash
git init
git add .
git commit -m "Initial SourceDNA MVP"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/sourcedna.git
git push -u origin main
```

Never commit `.env` or API keys.

## Cross-model compatibility

SourceDNA deliberately exposes two interfaces:

- **MCP** — for ChatGPT and any other host that supports remote/Streamable HTTP MCP.
- **REST/OpenAPI** — for LLM platforms that use tool/function calling rather than MCP.

This means SourceDNA is not tied to one LLM vendor. A model only needs to call `analyze_evidence` (MCP) or `/api/analyze` (REST) and render the returned evidence graph/metrics.

## Important limitations for the hackathon pitch

Be precise with judges:

- Similarity does not prove copying; it is evidence of derivation that SourceDNA visualizes for review.
- Publication dates are not available on every page and can be wrong.
- A source can cite another source without being fully dependent on it.
- A high EIS does not prove a claim is true.
- A low EIS does not prove a claim is false.
- Live discovery quality depends on the search provider and accessible webpages.
- Some sites block automated fetching, require JavaScript, or sit behind paywalls.

These are strengths of the pitch if stated correctly: SourceDNA is an **evidence-provenance layer**, not a magical truth detector.

## Recommended hackathon demo

1. Click the built-in synthetic-consensus demo.
2. Show “6 cited URLs” collapsing to only a small number of roots.
3. Show the lineage graph.
4. Explain EIS and claim drift.
5. Open ChatGPT with the SourceDNA MCP plugin connected.
6. Ask ChatGPT to call SourceDNA for a claim with several URLs.
7. End with: **“Eight citations do not necessarily mean eight sources.”**

## License

MIT
