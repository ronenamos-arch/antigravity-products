"""
image_downloader.py — Download product images from URLs into products/<slug>/images/
Returns list of local relative paths for use in HTML.
"""

import os
import re
import requests
from pathlib import Path


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.amazon.com/",
}

MAX_IMAGES = 8  # Cap to avoid bloat


def sanitize_filename(url: str, index: int) -> str:
    """Generate a clean sequential filename from image URL."""
    ext = ".jpg"
    match = re.search(r'\.(jpg|jpeg|png|webp)(\?|$)', url, re.IGNORECASE)
    if match:
        ext = "." + match.group(1).lower()
        if ext == ".webp":
            ext = ".jpg"  # Convert webp → jpg at download time
    return f"{index:02d}{ext}"


def download_images(image_urls: list, slug: str, products_dir: str = "products") -> list:
    """
    Download images to products/<slug>/images/
    Returns list of relative paths: ["images/01.jpg", "images/02.jpg", ...]
    """
    img_dir = Path(products_dir) / slug / "images"
    img_dir.mkdir(parents=True, exist_ok=True)

    local_paths = []
    urls_to_download = image_urls[:MAX_IMAGES]

    for i, url in enumerate(urls_to_download, start=1):
        filename = sanitize_filename(url, i)
        local_path = img_dir / filename

        if local_path.exists():
            print(f"[images] {filename} already exists, skipping")
            local_paths.append(f"images/{filename}")
            continue

        try:
            print(f"[images] Downloading {i}/{len(urls_to_download)}: {url[:80]}...")
            resp = requests.get(url, headers=HEADERS, timeout=15, stream=True)
            resp.raise_for_status()

            with open(local_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)

            local_paths.append(f"images/{filename}")
            print(f"[images] Saved → {local_path}")

        except Exception as e:
            print(f"[images] FAILED to download {url[:60]}: {e}")
            # Add placeholder entry so HTML still has a slot
            local_paths.append(None)

    return local_paths


if __name__ == "__main__":
    import sys, json
    raw_file = sys.argv[1]  # path to raw_product.json
    slug = sys.argv[2]
    with open(raw_file) as f:
        data = json.load(f)
    paths = download_images(data["images"], slug)
    print(f"\nDownloaded {len([p for p in paths if p])} images:")
    for p in paths:
        print(f"  {p}")
