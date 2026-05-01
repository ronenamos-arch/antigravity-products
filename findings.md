# 🔍 Discoveries & Findings

## Amazon Scraping Notes
- Amazon actively blocks simple requests with 503/captcha
- Best approach: `playwright` (headless browser) with stealth plugin, or `amazon-scraper` libraries
- Alternative: `scrapy-playwright` or `zenrows` proxy service
- Product images are in `#imgTagWrapperId` or `#altImages` — high-res via replacing `._AC_SX300_` with `._AC_SL1500_` in URL
- Bullet points: `#feature-bullets ul li`
- Title: `#productTitle`
- Video: embedded in `#dp-container` via iframe or JSON data in page source

## AliExpress Scraping Notes
- AliExpress requires JS rendering — playwright needed
- Images in `window.runParams.data.skuModule.imageModule.imagePathList` (JSON in page)
- Product title in `window.runParams.data.titleModule.subject`
- AliExpress images do not expire (unlike Amazon) but should still be downloaded locally

## PayPal Button Generation
- REST API: POST to `https://api-m.paypal.com/v1/payments/payment` (legacy) or Buttons API
- Simpler: PayPal Hosted Button — generate via `/v1/checkout/orders`
- Or: use static PayPal Buy Now URL format (no API key needed for basic):
  `https://www.paypal.com/cgi-bin/webscr?cmd=_xclick&business=EMAIL&amount=200&currency_code=ILS&item_name=NAME`
- Full API flow: Client Credentials → Access Token → Create Button → Get HTML

## GitHub Push via API
- Use `PyGithub` library or direct REST API
- Can create/update files via: `PUT /repos/:owner/:repo/contents/:path`
- Binary files (images) need base64 encoding
- Need: `GITHUB_TOKEN`, `GITHUB_REPO`, `GITHUB_OWNER` in .env

## Vercel Auto-Deploy
- Vercel watches GitHub repo — any push to main triggers redeploy automatically
- Each product at: `https://<repo-name>.vercel.app/products/<slug>/`
- Need `vercel.json` for routing (SPA or static file serving)

## Constraints
- Amazon image URLs with resize parameters (`._AC_`) must be normalized to get full-size
- Images must be saved as JPG/PNG — WebP may not render in all browsers (convert if needed)
- Hebrew text requires `dir="rtl"` on `<html>` and RTL-compatible CSS (text-align: right, flex-direction: row-reverse where needed)
- PayPal ILS (Israeli Shekel) support — verify currency code is accepted for seller's account region
