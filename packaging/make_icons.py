"""Derive platform icon formats (.ico, .icns) from the bundled 256px PNG.

Both are optional: when Pillow (or macOS ``iconutil``) is missing, the build
simply produces an executable with the default icon.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ICO_SIZES = [16, 24, 32, 48, 64, 128, 256]
ICNS_SIZES = [16, 32, 64, 128, 256, 512, 1024]


def _load_pillow():
    try:
        from PIL import Image  # noqa: PLC0415 — optional dependency
    except ImportError:
        return None
    return Image


def make_ico(source: Path, dest: Path) -> Path | None:
    image_mod = _load_pillow()
    if image_mod is None:
        print("[icons] Pillow not installed — skipping .ico", file=sys.stderr)
        return None
    with image_mod.open(source) as image:
        image.convert("RGBA").save(dest, format="ICO", sizes=[(s, s) for s in ICO_SIZES])
    print(f"[icons] wrote {dest}")
    return dest


def make_icns(source: Path, dest: Path) -> Path | None:
    if sys.platform != "darwin" or shutil.which("iconutil") is None:
        print("[icons] iconutil unavailable — skipping .icns", file=sys.stderr)
        return None
    image_mod = _load_pillow()
    if image_mod is None:
        print("[icons] Pillow not installed — skipping .icns", file=sys.stderr)
        return None

    with tempfile.TemporaryDirectory() as tmp:
        iconset = Path(tmp) / "icon.iconset"
        iconset.mkdir()
        with image_mod.open(source) as image:
            rgba = image.convert("RGBA")
            for size in ICNS_SIZES:
                resized = rgba.resize((size, size), image_mod.Resampling.LANCZOS)
                if size <= 512:
                    resized.save(iconset / f"icon_{size}x{size}.png")
                if size >= 32:
                    half = size // 2
                    resized.save(iconset / f"icon_{half}x{half}@2x.png")
        completed = subprocess.run(
            ["iconutil", "-c", "icns", str(iconset), "-o", str(dest)],
            check=False,
            capture_output=True,
            text=True,
        )
    if completed.returncode != 0:
        print(f"[icons] iconutil failed: {completed.stderr.strip()}", file=sys.stderr)
        return None
    print(f"[icons] wrote {dest}")
    return dest


def build_icons(source: Path, out_dir: Path) -> dict[str, Path | None]:
    out_dir.mkdir(parents=True, exist_ok=True)
    return {
        "ico": make_ico(source, out_dir / "repomanager.ico"),
        "icns": make_icns(source, out_dir / "repomanager.icns"),
    }


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    build_icons(root / "src" / "repomanager" / "ui" / "assets" / "icon.png", root / "build" / "icons")
