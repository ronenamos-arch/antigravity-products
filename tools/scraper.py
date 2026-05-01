"""
scraper.py — Extract product data + image URLs from Amazon or AliExpress.
Uses Playwright (headless Chromium) to handle JS-rendered pages.
Output: dict saved to .tmp/<slug>/raw_product.json
"""

import json
import re
import time
from pathlib import Path
from playwright.sync_api import sync_playwright


def detect_source(url: str) -> str:
    if "amazon" in url:
        return "amazon"
    if "aliexpress" in url:
        return "aliexpress"
    raise ValueError(f"Unsupported URL: {url}. Only Amazon and AliExpress supported.")


def scrape_amazon(page) -> dict:
    data = {}

    try:
        data["title"] = page.locator("#productTitle").inner_text().strip()
    except Exception:
        data["title"] = ""

    bullets = []
    try:
        items = page.locator("#feature-bullets ul li span.a-list-item").all()
        bullets = [b.inner_text().strip() for b in items if b.inner_text().strip()]
    except Exception:
        pass
    data["bullets"] = bullets

    try:
        data["description"] = page.locator("#productDescription").inner_text().strip()
    except Exception:
        data["description"] = ""

    images = []
    try:
        content = page.content()
        match = re.search(r"'colorImages'.*?:\s*\{.*?'initial'\s*:\s*(\[.*?\])\s*\}", content, re.DOTALL)
        if not match:
            match = re.search(r'"colorImages".*?:\s*\{.*?"initial"\s*:\s*(\[.*?\])\s*\}', content, re.DOTALL)
        if match:
            img_data = json.loads(match.group(1))
            for img in img_data:
                url_hi = img.get("hiRes") or img.get("large") or img.get("main") or ""
                if url_hi and url_hi not in images:
                    images.append(url_hi)
    except Exception:
        pass

    if not images:
        try:
            thumbs = page.locator("#altImages img").all()
            for thumb in thumbs:
                src = thumb.get_attribute("src") or ""
                full = re.sub(r'\._[A-Z]{2}\d+_\.', "._AC_SL1500_.", src)
                full = re.sub(r'\._[A-Z]{2}\d+,\d+_\.', "._AC_SL1500_.", full)
                if full and "sprite" not in full and full not in images:
                    images.append(full)
        except Exception:
            pass

    if not images:
        try:
            src = page.locator("#landingImage").get_attribute("src") or ""
            if src:
                images.append(src)
        except Exception:
            pass

    data["images"] = images

    video_url = None
    try:
        content = page.content()
        match = re.search(r'"url"\s*:\s*"(https?://[^"]+\.mp4[^"]*)"', content)
        if match:
            video_url = match.group(1)
    except Exception:
        pass
    data["video_url"] = video_url

    try:
        price_el = page.locator(".a-price .a-offscreen").first
        data["original_price"] = price_el.inner_text().strip()
    except Exception:
        data["original_price"] = ""

    data["source"] = "amazon"
    return data


def scrape_aliexpress(page) -> dict:
    """Extract product data from AliExpress — only real product images."""
    data = {}

    try:
        # Get title from runParams
        run_params = page.evaluate("() => { try { return JSON.parse(JSON.stringify(window.runParams)); } catch(e) { return null; } }")
        data_obj = (run_params or {}).get("data", {})
        title_module = data_obj.get("titleModule", {})
        data["title"] = title_module.get("subject", "") or page.title()
        data["description"] = ""
        data["bullets"] = []

        # Price
        price_module = data_obj.get("priceModule", {})
        data["original_price"] = str(price_module.get("minAmount", {}).get("value", ""))

        # ── IMAGES: only large rendered product photos ──
        # Scroll to trigger lazy loading of gallery
        page.evaluate("window.scrollTo(0, 300)")
        page.wait_for_timeout(2500)
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(1000)

        # Get all images with naturalWidth >= 200 (real product photos, not icons)
        images = page.evaluate("""() => {
            return Array.from(document.images)
                .filter(img => img.naturalWidth >= 200 && img.naturalHeight >= 200)
                .map(img => img.src)
                .filter(src => src && (src.includes('alicdn.com') || src.includes('aliexpress')));
        }""")

        # Also try data-src for lazy-loaded images
        lazy_imgs = page.evaluate("""() => {
            return Array.from(document.querySelectorAll('img[data-src*="alicdn.com"]'))
                .map(img => img.getAttribute('data-src'))
                .filter(Boolean);
        }""")
        for src in lazy_imgs:
            if src and src not in images:
                images.append(src)

        # Normalize and filter
        clean_images = []
        seen = set()
        SKIP_KEYWORDS = ['icon', 'logo', 'flag', 'star', 'rating', 'avatar',
                         'payment', 'trustmark', 'shipping', 'coin', 'badge']
        for img in images:
            if img.startswith("//"):
                img = "https:" + img
            lower = img.lower()
            if any(kw in lower for kw in SKIP_KEYWORDS):
                continue
            # Strip query params — AliExpress ?ver=...avif serves tiny thumbnails
            img = img.split("?")[0]
            # Strip size markers from filename to get original resolution
            img = re.sub(r'_\d+x\d+(\.\w{3,4})$', r'\1', img)
            img = re.sub(r'_\d+x\d+q\d+(\.\w{3,4})$', r'\1', img)
            if img not in seen:
                seen.add(img)
                clean_images.append(img)

        data["images"] = clean_images[:10]

    except Exception as e:
        data["title"] = page.title()
        data["description"] = ""
        data["bullets"] = []
        data["images"] = []
        data["original_price"] = ""
        data["error"] = str(e)

    data["video_url"] = None
    data["source"] = "aliexpress"
    return data


def scrape_product(url: str, slug: str, tmp_dir: str = ".tmp") -> dict:
    source = detect_source(url)
    out_dir = Path(tmp_dir) / slug
    out_dir.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800},
            locale="en-US",
        )
        page = context.new_page()

        print(f"[scraper] Loading {source} page...")
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        time.sleep(3)

        if source == "amazon":
            data = scrape_amazon(page)
        else:
            data = scrape_aliexpress(page)

        browser.close()

    data["url"] = url
    data["slug"] = slug

    out_file = out_dir / "raw_product.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"[scraper] Saved raw data → {out_file}")
    print(f"[scraper] Found {len(data['images'])} images, title: {data['title'][:60]}...")
    return data


if __name__ == "__main__":
    import sys
    url = sys.argv[1]
    slug = sys.argv[2] if len(sys.argv) > 2 else "test-product"
    scrape_product(url, slug)
