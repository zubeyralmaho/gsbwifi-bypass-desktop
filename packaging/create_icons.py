"""
Icon üretici — assets/ klasörüne platform ikonlarını oluşturur.

Kullanım:
    python packaging/create_icons.py

Çıktılar:
    assets/icon.png   — 256×256 PNG (tüm platformlar)
    assets/icon.ico   — Windows (16/32/48/256 px)
    assets/icon.icns  — macOS (iconutil ile, sadece macOS'ta)
"""
import os
import platform
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("[Hata] Pillow yüklü değil. Çalıştırın: pip install pillow", file=sys.stderr)
    sys.exit(1)

ASSETS_DIR = Path(__file__).parent.parent / "assets"
ASSETS_DIR.mkdir(parents=True, exist_ok=True)


def create_icon_image(size: int = 256) -> Image.Image:
    """Yeşil daire + beyaz 'W' harfi içeren kare PNG üretir."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Arka plan dairesi
    margin = int(size * 0.04)
    draw.ellipse(
        [margin, margin, size - margin, size - margin],
        fill="#2ecc71",
    )

    # "W" harfi
    font_size = int(size * 0.52)
    font = None
    font_candidates = [
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
    ]
    for candidate in font_candidates:
        if Path(candidate).exists():
            try:
                font = ImageFont.truetype(candidate, font_size)
                break
            except OSError:
                continue

    text = "W"
    if font:
        bbox = draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        x = (size - tw) / 2 - bbox[0]
        y = (size - th) / 2 - bbox[1]
        draw.text((x, y), text, fill="white", font=font)
    else:
        # Fallback: varsayılan font
        bbox = draw.textbbox((0, 0), text)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        draw.text(((size - tw) / 2, (size - th) / 2), text, fill="white")

    return img


def create_png() -> Path:
    out = ASSETS_DIR / "icon.png"
    img = create_icon_image(256)
    img.save(out, "PNG")
    print(f"[OK] {out}")
    return out


def create_ico() -> Path:
    out = ASSETS_DIR / "icon.ico"
    sizes = [16, 32, 48, 256]
    images = [create_icon_image(s).convert("RGBA") for s in sizes]
    images[0].save(
        out,
        format="ICO",
        sizes=[(s, s) for s in sizes],
        append_images=images[1:],
    )
    print(f"[OK] {out}")
    return out


def create_icns() -> Path:
    """macOS iconutil kullanarak .icns üretir."""
    out = ASSETS_DIR / "icon.icns"

    if platform.system() != "Darwin":
        print("[Atlandı] .icns üretimi sadece macOS'ta desteklenir.", file=sys.stderr)
        return out

    if not shutil.which("iconutil"):
        print("[Uyarı] iconutil bulunamadı; .icns üretilemedi.", file=sys.stderr)
        return out

    iconset_sizes = {
        "icon_16x16.png": 16,
        "icon_16x16@2x.png": 32,
        "icon_32x32.png": 32,
        "icon_32x32@2x.png": 64,
        "icon_128x128.png": 128,
        "icon_128x128@2x.png": 256,
        "icon_256x256.png": 256,
        "icon_256x256@2x.png": 512,
        "icon_512x512.png": 512,
        "icon_512x512@2x.png": 1024,
    }

    with tempfile.TemporaryDirectory() as tmp:
        iconset_dir = Path(tmp) / "AppIcon.iconset"
        iconset_dir.mkdir()
        for filename, size in iconset_sizes.items():
            img = create_icon_image(size)
            img.save(iconset_dir / filename, "PNG")

        result = subprocess.run(
            ["iconutil", "-c", "icns", str(iconset_dir), "-o", str(out)],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print(f"[Hata] iconutil: {result.stderr}", file=sys.stderr)
        else:
            print(f"[OK] {out}")

    return out


if __name__ == "__main__":
    create_png()
    create_ico()
    create_icns()
    print("\nİkon üretimi tamamlandı.")
