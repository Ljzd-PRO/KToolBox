from __future__ import annotations

import argparse
import json
from pathlib import Path

from ktoolbox.configuration import RuntimeContext
from ktoolbox.webui.app import create_app

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "webui" / "openapi.json"


def render_openapi() -> str:
    """Render the FastAPI contract in a stable, reviewable form."""
    app = create_app(RuntimeContext.from_project(ROOT))
    return json.dumps(app.openapi(), ensure_ascii=True, indent=2, sort_keys=True) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Export the deterministic KToolBox WebUI OpenAPI contract")
    parser.add_argument("--check", action="store_true", help="fail when the committed contract is stale")
    arguments = parser.parse_args()
    rendered = render_openapi()
    if arguments.check:
        if not OUTPUT.is_file() or OUTPUT.read_text(encoding="utf-8") != rendered:
            parser.error(f"{OUTPUT.relative_to(ROOT)} is stale; regenerate the WebUI API contract")
        return 0
    OUTPUT.write_text(rendered, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
