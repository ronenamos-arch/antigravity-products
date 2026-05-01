# 📜 gemini.md — The Project Law

## North Star
Run `python make_site.py <url> --price <ILS>` → get a full Hebrew conversion-optimized product page, images saved locally, pushed to GitHub, deployed to Vercel, with a live PayPal Buy Now button.

## Integrations
| Service | Purpose | Status |
|---|---|---|
| Amazon / AliExpress | Source of product data + images | Scraping via requests/playwright |
| PayPal API | Generate Buy Now button per product | Client ID + Secret → .env (TBD) |
| GitHub API | Push product folder + HTML to repo | Token → .env (TBD) |
| Vercel | Auto-deploy on GitHub push | Connected to repo (TBD) |
| Claude API | Generate Hebrew marketing copy | Optional enhancement |

## CLI Interface
```
python make_site.py <product_url> --price <ILS_price> [--name <slug>]
```
- `product_url` — Amazon or AliExpress product page
- `--price` — selling price in ILS (e.g. 200)
- `--name` — optional slug override (default: auto-generated from product title)

## Data Schemas (The Payload)

### Input (CLI)
```json
{
  "product_url": "https://www.amazon.com/dp/...",
  "price_ils": 200,
  "product_slug": "bath-eggs-kids"
}
```

### Scraped Product Data (Intermediate — .tmp/)
```json
{
  "title_original": "Bath Bomb Eggs for Kids 12 Pack...",
  "description_original": "...",
  "bullet_points": ["bullet1", "bullet2"],
  "images": [
    { "url": "https://...", "local_path": "products/bath-eggs-kids/img/01.jpg" }
  ],
  "video_url": "https://... or null",
  "original_price": "$24.99",
  "source": "amazon"
}
```

### Output — Product Folder Structure
```
products/
└── <product_slug>/
    ├── index.html        ← Full Hebrew sales page
    ├── images/
    │   ├── 01.jpg
    │   ├── 02.jpg
    │   └── ...
    └── product.json      ← Metadata for reference
```

### PayPal Button Output
```json
{
  "button_html": "<form action='https://www.paypal.com/...'> ... </form>",
  "button_url": "https://www.paypal.com/...",
  "item_name": "Hebrew product name",
  "amount": "200.00",
  "currency": "ILS"
}
```

## Page Structure (Fixed Template)
1. כותרת עליונה (Headline)
2. תת-כותרת שיווקית
3. תמונה ראשית (IMAGE_1)
4. תיאור קצר וממוקד
5. יתרונות מרכזיים (bullets)
6. מה מקבלים בערכה
7. IMAGE_2
8. איך זה עובד (4 שלבים)
9. VIDEO_1 placeholder
10. למי זה מתאים
11. בטיחות והרכב
12. IMAGE_4
13. הצעה מיוחדת — מחיר מקורי vs. מחיר מבצע + כפתור PayPal
14. FAQ (5 שאלות)

## Behavioral Rules
1. All page text must be in Hebrew only — no English visible to end user.
2. Direction: `dir="rtl"`, font: Heebo or Assistant (Google Fonts).
3. Never auto-send payments — PayPal button only, user clicks manually.
4. Images are downloaded locally, never hotlinked from Amazon/AliExpress (they expire).
5. If an image fails to download, insert a visible placeholder div — never crash.
6. If no video found, VIDEO_1 section is hidden, not broken.
7. Product slug must be URL-safe (lowercase, hyphens only).
8. Never overwrite an existing product folder — prompt user or error out.
9. Page must be mobile-first, responsive.
10. Conversion design: dark CTA button (#FF6B00 or deep green), urgency text, price comparison strikethrough.

## GitHub Repo Structure (TBD — pending user confirmation)
```
antigravity-products/        ← repo name TBD
├── products/
│   └── <product-slug>/
│       ├── index.html
│       └── images/
├── vercel.json              ← routing config
└── README.md
```

## Maintenance Log
- 2026-03-16: Blueprint initialized. Awaiting: GitHub repo name, PayPal credentials, price CLI confirmation.
