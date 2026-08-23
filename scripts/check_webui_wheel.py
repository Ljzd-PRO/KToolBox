from __future__ import annotations

import ast
from email.parser import Parser
from pathlib import Path
from zipfile import ZipFile


def _source_version() -> str:
    init_path = Path(__file__).resolve().parents[1] / "ktoolbox" / "__init__.py"
    module = ast.parse(init_path.read_text(encoding="utf-8"), filename=str(init_path))
    for statement in module.body:
        if not isinstance(statement, ast.Assign):
            continue
        if any(isinstance(target, ast.Name) and target.id == "__version__" for target in statement.targets):
            version = ast.literal_eval(statement.value)
            if isinstance(version, str) and version:
                return version.lstrip("v")
    raise SystemExit("could not read the KToolBox source version")


def main() -> int:
    source_version = _source_version()
    wheels = sorted(Path("dist").glob(f"ktoolbox-{source_version}-*.whl"))
    if len(wheels) != 1:
        raise SystemExit(f"expected exactly one KToolBox wheel, found {len(wheels)}")
    with ZipFile(wheels[0]) as archive:
        names = set(archive.namelist())
        metadata_files = sorted(name for name in names if name.endswith(".dist-info/METADATA"))
        if len(metadata_files) != 1:
            raise SystemExit(f"expected exactly one wheel metadata file, found {len(metadata_files)}")
        metadata = archive.read(metadata_files[0]).decode("utf-8")
    package_metadata = Parser().parsestr(metadata)
    if (package_metadata["Name"] or "").casefold() != "ktoolbox":
        raise SystemExit("wheel metadata does not describe KToolBox")
    version = package_metadata["Version"]
    if version != source_version or not wheels[0].name.startswith(f"ktoolbox-{version}-"):
        raise SystemExit("wheel filename and metadata version do not match")
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
