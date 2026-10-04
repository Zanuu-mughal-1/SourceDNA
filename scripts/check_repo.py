from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
required = [
    'backend/sourcedna/app.py','backend/sourcedna/analysis.py','frontend/src/main.jsx',
    'plugin/sourcedna-plugin/plugin.json','plugin/sourcedna-plugin/mcp.json.template','Dockerfile','README.md'
]
missing = [p for p in required if not (ROOT/p).exists()]
if missing:
    raise SystemExit('Missing: ' + ', '.join(missing))
manifest = json.loads((ROOT/'plugin/sourcedna-plugin/plugin.json').read_text())
assert manifest['name'] == 'sourcedna'
assert len(manifest['extensions']['com.openai']['interface']['shortDescription']) <= 30
print('Repository structure: OK')
