from __future__ import annotations

import argparse
import json
import shutil
import tempfile
import zipfile
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "plugin" / "sourcedna-plugin"
OUT_DIR = ROOT / "dist"


def main():
    p = argparse.ArgumentParser(description="Build a SourceDNA Agent Plugin ZIP for a deployed MCP endpoint.")
    p.add_argument("--mcp-url", required=True, help="Public HTTPS endpoint, e.g. https://sourcedna.example.com/mcp")
    p.add_argument("--output", default=str(OUT_DIR / "sourcedna-plugin.zip"))
    args = p.parse_args()

    u = urlparse(args.mcp_url)
    if u.scheme != "https" or not u.netloc or not u.path.rstrip('/').endswith('/mcp'):
        raise SystemExit("--mcp-url must be a public HTTPS URL ending in /mcp")

    out = Path(args.output).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as td:
        root = Path(td) / "sourcedna"
        shutil.copytree(SOURCE, root)
        template = (root / "mcp.json.template").read_text()
        (root / "mcp.json").write_text(template.replace("__MCP_URL__", args.mcp_url.rstrip('/')))
        (root / "mcp.json.template").unlink()

        manifest = json.loads((root / "plugin.json").read_text())
        assert manifest["name"] == "sourcedna"
        short = manifest["extensions"]["com.openai"]["interface"]["shortDescription"]
        if len(short) > 30:
            raise SystemExit("Plugin shortDescription exceeds 30 characters")

        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
            for f in root.rglob("*"):
                if f.is_file():
                    z.write(f, Path("sourcedna") / f.relative_to(root))
    print(out)

if __name__ == "__main__":
    main()
