from __future__ import annotations

from pathlib import Path
from zipfile import ZipFile

from ktoolbox import __version__


def main() -> int:
    version = __version__.lstrip("v")
    wheels = sorted(Path("dist").glob(f"ktoolbox-{version}-*.whl"))
    if len(wheels) != 1:
        raise SystemExit(f"expected exactly one KToolBox wheel, found {len(wheels)}")
    with ZipFile(wheels[0]) as archive:
        names = set(archive.namelist())
    required = {
        "ktoolbox/webui/static/index.html",
        "ktoolbox/webui/app.py",
        "ktoolbox/webui/server.py",
        "webui/openapi.yaml",
    }
    missing = required - names
    if missing:
        raise SystemExit(f"wheel is missing WebUI files: {', '.join(sorted(missing))}")
    if not any(name.startswith("ktoolbox/webui/static/assets/") for name in names):
        raise SystemExit("wheel does not contain compiled WebUI assets")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
