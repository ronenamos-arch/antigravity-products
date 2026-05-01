# 📋 Project Task Plan — Website Maker

## Phase 1: Blueprint (Vision & Logic) ✅
- [x] North Star Defined — Hebrew product page from URL → GitHub → Vercel
- [x] CLI Interface Defined — `python make_site.py <url> --price <ILS>`
- [x] Page template structure confirmed (14-section Hebrew sales page)
- [x] Data Schema defined in gemini.md
- [x] Behavioral Rules set (RTL, Hebrew-only, no auto-send, local images)
- [ ] GitHub repo name confirmed (TBD)
- [ ] PayPal credentials in .env (TBD)
- [ ] Vercel connection confirmed (TBD)

## Phase 2: Link (Connectivity)
- [ ] Test Amazon scraping (requests + BeautifulSoup or Playwright)
- [ ] Test AliExpress scraping
- [ ] Test PayPal API — create Buy Now button
- [ ] Test GitHub API — push file to repo
- [ ] Verify Vercel auto-deploy fires on GitHub push

## Phase 3: Architect (The 3-Layer Build)
- [ ] `tools/scraper.py` — extract product data + images from URL
- [ ] `tools/image_downloader.py` — download and save images to product folder
- [ ] `tools/paypal_button.py` — generate Buy Now button HTML via PayPal API
- [ ] `tools/page_generator.py` — render Hebrew HTML from template + product data
- [ ] `tools/github_pusher.py` — commit and push product folder to GitHub
- [ ] `make_site.py` — main orchestrator (calls all tools in order)

## Phase 4: Stylize
- [ ] Hebrew conversion-optimized CSS (mobile-first, RTL, Heebo font)
- [ ] CTA button styling (high-contrast, urgency design)
- [ ] Image gallery component
- [ ] Review generated page in browser

## Phase 5: Trigger (Deployment)
- [ ] Confirm Vercel auto-deploy on GitHub push works end-to-end
- [ ] Test full flow: URL → local page → GitHub push → live Vercel URL
- [ ] Document usage in README
