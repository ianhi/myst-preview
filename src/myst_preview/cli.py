"""myst-preview CLI: Preview a single file rendered with MyST MD."""

from __future__ import annotations

import argparse
import os
import signal
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

SUPPORTED_EXTENSIONS = {".md", ".ipynb", ".rst", ".tex"}

MYST_YML_TEMPLATE = """\
version: 1
site:
  template: {theme}
project:
  toc:
    - file: {slug}
"""


def find_free_port(start: int, end: int = 0) -> int:
    """Find a free port starting from `start`, trying up to `end` (inclusive)."""
    if end == 0:
        end = start + 50
    for port in range(start, end + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("", port))
                return port
            except OSError:
                continue
    print(
        f"Error: no free port found in range {start}-{end}",
        file=sys.stderr,
    )
    sys.exit(1)


def wait_for_port(port: int, timeout: float = 30.0) -> bool:
    """Poll until a port is accepting connections, or timeout."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            if s.connect_ex(("127.0.0.1", port)) == 0:
                return True
        time.sleep(0.25)
    return False


def find_myst() -> list[str]:
    myst = shutil.which("myst")
    if myst:
        return [myst]
    npx = shutil.which("npx")
    if npx:
        return [npx, "-y", "mystmd"]
    print(
        "Error: 'myst' not found. Install with: npm install -g mystmd",
        file=sys.stderr,
    )
    sys.exit(1)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="myst-preview",
        description="Preview a single Markdown or Jupyter notebook file rendered with MyST MD.",
    )
    parser.add_argument(
        "file",
        help="File to preview (.md, .ipynb, .rst, .tex)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=3000,
        help="Port for the preview server (default: 3000)",
    )
    parser.add_argument(
        "--theme",
        default="book-theme",
        help="MyST site template (default: book-theme)",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Execute notebook/code cells",
    )
    parser.add_argument(
        "--build",
        action="store_true",
        help="Build static HTML instead of starting a live server",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Output directory for --build (default: ./_build/html)",
    )
    parser.add_argument(
        "--no-open",
        action="store_true",
        help="Don't open the preview in a browser",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {_get_version()}",
    )
    args = parser.parse_args(argv)

    source = Path(args.file).resolve()
    if not source.exists():
        print(f"Error: {args.file} does not exist", file=sys.stderr)
        sys.exit(1)
    if source.suffix not in SUPPORTED_EXTENSIONS:
        exts = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        print(
            f"Error: unsupported file type '{source.suffix}'. Supported: {exts}",
            file=sys.stderr,
        )
        sys.exit(1)

    source_dir = source.parent
    slug = source.stem

    tmpdir = tempfile.mkdtemp(prefix="myst-preview-")
    proc = None

    def cleanup(*_: object) -> None:
        nonlocal proc
        if proc and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
            proc = None
        shutil.rmtree(tmpdir, ignore_errors=True)

    def cleanup_and_exit(*_: object) -> None:
        cleanup()
        sys.exit(0)

    signal.signal(signal.SIGINT, cleanup_and_exit)
    signal.signal(signal.SIGTERM, cleanup_and_exit)

    try:
        # Symlink everything from the source directory so relative paths work.
        for item in source_dir.iterdir():
            if item.name.startswith("."):
                continue
            target = Path(tmpdir) / item.name
            if not target.exists():
                os.symlink(item, target)

        # Write our own myst.yml (replace any symlinked one).
        myst_yml = Path(tmpdir) / "myst.yml"
        if myst_yml.is_symlink():
            myst_yml.unlink()
        myst_yml.write_text(
            MYST_YML_TEMPLATE.format(theme=args.theme, slug=slug)
        )

        myst_cmd = find_myst()

        if args.build:
            cmd = [*myst_cmd, "build", "--html"]
            if args.execute:
                cmd.append("--execute")
            print(f"Building {source.name} to static HTML...")
            result = subprocess.run(cmd, cwd=tmpdir)
            if result.returncode == 0:
                build_dir = Path(tmpdir) / "_build" / "html"
                output_dir = (
                    Path(args.output) if args.output else Path.cwd() / "_build" / "html"
                )
                if output_dir.exists():
                    shutil.rmtree(output_dir)
                shutil.copytree(build_dir, output_dir)
                print(f"Output written to {output_dir}")
            sys.exit(result.returncode)
        else:
            port = find_free_port(args.port)
            if port != args.port:
                print(f"Port {args.port} is in use, using {port} instead.")

            cmd = [*myst_cmd, "start", "--port", str(port), "--keep-host"]
            if args.execute:
                cmd.append("--execute")

            # Bind to all interfaces so the preview is reachable over the network.
            env = {**os.environ, "HOST": "0.0.0.0"}

            print(f"Starting MyST preview of {source.name}")
            print("Press Ctrl+C to stop.\n")

            proc = subprocess.Popen(cmd, cwd=tmpdir, env=env)

            if not args.no_open:
                import webbrowser

                if wait_for_port(port):
                    webbrowser.open(f"http://localhost:{port}")

            proc.wait()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
    finally:
        cleanup()


def _get_version() -> str:
    from myst_preview import __version__

    return __version__
