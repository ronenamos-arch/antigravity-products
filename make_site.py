#!/usr/bin/env python
"""
make_site.py — Main orchestrator.
Usage: python make_site.py <product_url> --price <ILS> [--name <slug>]

Steps:
  1. Scrape product URL (Amazon / AliExpress)
  2. Download images to products/<slug>/images/
  3. Generate PayPal Buy Now button
  4. Generate full Hebrew HTML page
  5. Push to GitHub → Vercel auto-deploys
"""

import argparse
import json
import re
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

# Add tools/ to path
sys.path.insert(0, str(Path(__file__).parent / "tools"))

from scraper import scrape_product
from image_downloader import download_images
from paypal_button import generate_paypal_button
from page_generator import generate_page, save_page
from github_pusher import push_product


PRODUCTS_DIR = Path(__file__).parent / "products"
TMP_DIR = Path(__file__).parent / ".tmp"


def slugify(text: str) -> str:
    """Convert product title to URL-safe ASCII slug. Returns empty string if title is non-ASCII."""
    text = text.lower()
    text = re.sub(r'[^\x00-\x7F]+', '', text)  # Strip non-ASCII (Hebrew, etc.)
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    text = re.sub(r'-+', '-', text)
    return text[:50].strip('-')


def extract_item_id(url: str) -> str:
    """Extract item ID from AliExpress URL as fallback slug."""
    match = re.search(r'/item/(\d+)', url)
    if match:
        return f"item-{match.group(1)}"
    match = re.search(r'orig_sl_item_id%3A(\d+)', url)
    if match:
        return f"item-{match.group(1)}"
    return ""


def confirm_overwrite(slug: str) -> bool:
    product_path = PRODUCTS_DIR / slug
    if product_path.exists():
        answer = input(f"\n⚠️  Folder 'products/{slug}' already exists. Overwrite? [y/N]: ").strip().lower()
        return answer == "y"
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Generate a Hebrew product sales page from Amazon/AliExpress URL"
    )
    parser.add_argument("url", help="Amazon or AliExpress product URL")
    parser.add_argument("--price", type=float, required=True, help="Selling price in ILS (e.g. 200)")
    parser.add_argument("--original-price", type=float, default=None,
                        help="Crossed-out original price in ILS (default: price × 1.4)")
    parser.add_argument("--name", type=str, default=None,
                        help="Product slug override (e.g. bath-eggs-kids). Auto-generated if omitted.")
    parser.add_argument("--no-push", action="store_true",
                        help="Skip GitHub push (local preview only)")
    args = parser.parse_args()

    print("\n" + "═" * 55)
    print("  Website Maker — Hebrew Product Page Generator")
    print("═" * 55)
    print(f"  URL:   {args.url[:70]}")
    print(f"  Price: {int(args.price)} ₪")
    print("═" * 55 + "\n")

    # ── STEP 1: SCRAPE ──────────────────────────────────────
    print("📡 Step 1/5 — Scraping product page...")
    raw_data = scrape_product(args.url, slug="__temp__", tmp_dir=str(TMP_DIR))

    # Determine slug
    if args.name:
        slug = slugify(args.name)
    else:
        # Try ASCII slug from title first
        slug = slugify(raw_data.get("title", ""))
        if not slug:
            # Non-ASCII title (Hebrew) — use item ID
            slug = extract_item_id(args.url) or "product"
            print(f"\n  💡 Tip: pass --name bath-bombs to give this a friendlier URL")
            print(f"     Using: {slug}")

    print(f"\n  Slug: {slug}")
    raw_data["slug"] = slug

    # Re-save with correct slug
    slug_tmp = TMP_DIR / slug
    slug_tmp.mkdir(parents=True, exist_ok=True)
    with open(slug_tmp / "raw_product.json", "w", encoding="utf-8") as f:
        json.dump(raw_data, f, ensure_ascii=False, indent=2)

    # Overwrite guard
    if not confirm_overwrite(slug):
        print("Aborted.")
        sys.exit(0)

    # ── STEP 2: DOWNLOAD IMAGES ──────────────────────────────
    print("\n🖼️  Step 2/5 — Downloading images...")
    image_paths = download_images(
        raw_data.get("images", []),
        slug,
        products_dir=str(PRODUCTS_DIR)
    )
    valid_images = [p for p in image_paths if p]
    print(f"  Downloaded {len(valid_images)}/{len(image_paths)} images")

    if not valid_images:
        print("  ⚠️  No images downloaded — page will use placeholders")

    # ── STEP 3: PAYPAL BUTTON ────────────────────────────────
    print("\n💳 Step 3/5 — Generating PayPal button...")
    item_name = raw_data.get("title", "מוצר")[:127]  # PayPal 127 char limit
    paypal_result = generate_paypal_button(item_name, args.price)
    print(f"  Button URL: {paypal_result['button_url'][:80]}...")

    # ── STEP 4: GENERATE PAGE ────────────────────────────────
    print("\n🏗️  Step 4/5 — Generating Hebrew HTML page...")
    html = generate_page(
        product_data=raw_data,
        image_paths=valid_images,
        paypal_html=paypal_result["button_html"],
        price_ils=args.price,
        original_price_ils=args.original_price,
        products_dir=str(PRODUCTS_DIR),
    )
    out_file = save_page(html, slug, products_dir=str(PRODUCTS_DIR))

    # Save product metadata
    meta = {
        "slug": slug,
        "url": args.url,
        "price_ils": args.price,
        "title": raw_data.get("title", ""),
        "images": valid_images,
        "source": raw_data.get("source", ""),
    }
    with open(PRODUCTS_DIR / slug / "product.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    print(f"\n  ✅ Page saved: {out_file}")

    # ── STEP 5: PUSH TO GITHUB ───────────────────────────────
    if args.no_push:
        print("\n⏭️  Step 5/5 — Skipping GitHub push (--no-push)")
        print(f"\n  Local preview: open '{out_file}' in browser")
    else:
        print("\n🚀 Step 5/5 — Pushing to GitHub...")
        try:
            live_url = push_product(slug, products_dir=str(PRODUCTS_DIR))
            print("\n" + "═" * 55)
            print("  DONE!")
            print(f"  Live URL (after Vercel deploys ~30s):")
            print(f"  {live_url}")
            print("═" * 55 + "\n")
        except Exception as e:
            print(f"\n  ❌ GitHub push failed: {e}")
            print(f"  Page is ready locally: {out_file}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
