from __future__ import annotations

import argparse
import os
import re
import signal
import socket
import subprocess
import tempfile
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

from ktoolbox import __version__


def _available_loopback_port() -> int:
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return int(listener.getsockname()[1])


def _wait_for_webui(process: subprocess.Popen[str], base_url: str, timeout: float) -> None:
    deadline = time.monotonic() + timeout
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        if process.poll() is not None:
            output = process.communicate()[0]
            raise RuntimeError(f"WebUI executable exited before startup:\n{output[-8000:]}")
        try:
            with urlopen(f"{base_url}/", timeout=2) as response:  # noqa: S310 - fixed loopback URL
                html = response.read().decode("utf-8")
                if response.status != 200 or 'id="root"' not in html:
                    raise RuntimeError("WebUI root did not return the packaged application shell")
                if response.headers.get("X-Frame-Options") != "DENY":
                    raise RuntimeError("WebUI root is missing the expected security headers")
            asset_match = re.search(r'(?:src|href)="(/assets/[^"]+)"', html)
            if asset_match is None:
                raise RuntimeError("WebUI root does not reference a packaged asset")
            with urlopen(f"{base_url}{asset_match.group(1)}", timeout=5) as response:  # noqa: S310
                if response.status != 200 or not response.read(1):
                    raise RuntimeError("WebUI packaged asset could not be read")
            return
        except (OSError, RuntimeError, URLError) as exc:
            last_error = exc
            time.sleep(0.25)
    raise TimeoutError(f"WebUI did not start within {timeout:.0f}s: {last_error}")


def _stop_process_tree(process: subprocess.Popen[str], *, windows: bool | None = None) -> None:
    """Stop the packaged server and every child that inherited its output pipe."""
    if process.poll() is not None:
        process.communicate()
        return

    is_windows = os.name == "nt" if windows is None else windows
    try:
        if is_windows:
            process.send_signal(signal.CTRL_BREAK_EVENT)
        else:
            os.killpg(process.pid, signal.SIGTERM)
        process.communicate(timeout=20)
        return
    except (OSError, subprocess.TimeoutExpired):
        pass

    if is_windows:
        subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
            check=False,
            capture_output=True,
            text=True,
            timeout=20,
        )
    else:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    process.communicate(timeout=20)


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke-test a packaged KToolBox executable")
    parser.add_argument("executable", type=Path)
    parser.add_argument("--port", type=int, default=0)
    parser.add_argument("--timeout", type=float, default=90)
    args = parser.parse_args()

    executable = args.executable.resolve()
    version = subprocess.run(
        [str(executable), "--version"],
        check=True,
        capture_output=True,
        text=True,
        timeout=args.timeout,
    ).stdout.strip()
    if version != __version__:
        raise RuntimeError(f"packaged version {version!r} does not match source version {__version__!r}")

    env = os.environ.copy()
    env.update(
        {
            "KTOOLBOX_WEBUI__USERNAME": "release-smoke",
            "KTOOLBOX_WEBUI__PASSWORD": "release-smoke-password",
            "NO_COLOR": "1",
        }
    )
    port = args.port or _available_loopback_port()
    base_url = f"http://127.0.0.1:{port}"
    with tempfile.TemporaryDirectory(prefix="ktoolbox-release-smoke-") as project_dir:
        process = subprocess.Popen(
            [
                str(executable),
                "webui",
                project_dir,
                "--host",
                "127.0.0.1",
                "--port",
                str(port),
                "--no-open",
            ],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0,
            start_new_session=os.name != "nt",
        )
        try:
            _wait_for_webui(process, base_url, args.timeout)
        finally:
            _stop_process_tree(process)
    print(f"Packaged KToolBox {version} served its embedded WebUI successfully")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
