"""
page_generator.py — Generate a full Hebrew sales page HTML from product data.
Modern high-conversion design: dark hero, sticky image gallery, FAQ accordion.
"""

import json
from pathlib import Path


def img_tag(local_path, alt="", css_class="product-img"):
    if local_path:
        return f'<img src="{local_path}" alt="{alt}" class="{css_class}" loading="lazy">'
    return '<div class="img-placeholder"><span>תמונה בקרוב</span></div>'


def generate_page(product_data, image_paths, paypal_html,
                  price_ils, original_price_ils=None, products_dir="products"):

    title = product_data.get("title", "")
    bullets = product_data.get("bullets", [])
    video_url = product_data.get("video_url")

    if original_price_ils is None:
        original_price_ils = round(price_ils * 1.4)

    valid_images = [p for p in image_paths if p]

    # Benefits list
    if bullets:
        items = "".join(f'<li><span class="check">✓</span>{b}</li>' for b in bullets[:6])
        bullets_html = f'<ul class="benefits-list">{items}</ul>'
    else:
        bullets_html = (
            '<ul class="benefits-list">'
            '<li><span class="check">✓</span>חוויה של &ldquo;וואו&rdquo; בכל אמבט</li>'
            '<li><span class="check">✓</span>מתאים כמתנה לפסח, יום הולדת וסוף שבוע</li>'
            '<li><span class="check">✓</span>הופך ילדים שלא אוהבים אמבטיה לרגע שמחכים לו</li>'
            '<li><span class="check">✓</span>רעיון מתנה מקורי, טרנדי ומצטלם מושלם</li>'
            '</ul>'
        )

    # Thumbnail gallery
    gallery_html = ""
    for i, path in enumerate(valid_images[:6]):
        active = "active" if i == 0 else ""
        gallery_html += (
            f'<div class="thumb {active}" onclick="setMain(this)" data-src="{path}">'
            f'<img src="{path}" alt="תמונה {i+1}"></div>'
        )

    main_img_src = valid_images[0] if valid_images else ""
    main_img_html = (
        f'<img id="mainImg" src="{main_img_src}" alt="{title}">'
        if main_img_src else
        '<div class="img-placeholder"><span>תמונה בקרוב</span></div>'
    )

    video_section = ""
    if video_url:
        video_section = (
            '<section class="section"><h2>צפו בפעולה</h2>'
            f'<video controls class="product-video"><source src="{video_url}" type="video/mp4"></video>'
            '</section>'
        )

    price_per_unit = f"{price_ils / 12:.0f}" if price_ils else ""
    discount_pct = round((1 - price_ils / original_price_ils) * 100) if original_price_ils else 30
    price_per_line = f'<div class="price-per-unit">פחות מ-{price_per_unit} &#8362; ליחידה</div>' if price_per_unit else ""
    sub_price_txt = f'פחות מ-{price_per_unit} &#8362; ליחידה &middot; ' if price_per_unit else ""
    savings = int(original_price_ils - price_ils)

    css = """
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    :root {
      --orange: #FF6B00; --dark: #0d0d1a; --dark2: #1a1a2e;
      --text: #1a1a1a; --muted: #666; --border: #e8e8e8; --green: #00b341;
    }
    body { font-family: 'Heebo', sans-serif; direction: rtl; background: #f7f7f9; color: var(--text); font-size: 16px; line-height: 1.6; }

    .topbar { background: var(--orange); color: white; text-align: center; padding: 10px 16px; font-size: 0.9rem; font-weight: 700; }

    .hero { background: linear-gradient(160deg, var(--dark) 0%, var(--dark2) 60%, #0f3460 100%); color: white; padding: 50px 20px 60px; text-align: center; position: relative; overflow: hidden; }
    .hero::before { content: ''; position: absolute; inset: 0; background: radial-gradient(ellipse at 50% 0%, rgba(255,107,0,0.15) 0%, transparent 70%); }
    .hero-inner { position: relative; z-index: 1; max-width: 800px; margin: 0 auto; }
    .badge-row { display: flex; gap: 10px; justify-content: center; flex-wrap: wrap; margin-bottom: 24px; }
    .badge { display: inline-flex; align-items: center; gap: 6px; background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2); color: white; padding: 6px 14px; border-radius: 50px; font-size: 0.82rem; font-weight: 600; }
    .badge.hot { background: var(--orange); border-color: var(--orange); }
    .hero h1 { font-size: clamp(1.7rem, 5vw, 2.8rem); font-weight: 900; line-height: 1.2; margin-bottom: 16px; }
    .hero .subtitle { font-size: clamp(1rem, 2.5vw, 1.25rem); font-weight: 300; opacity: 0.85; max-width: 600px; margin: 0 auto 32px; }
    .hero-cta { display: inline-block; background: var(--orange); color: white; padding: 16px 40px; border-radius: 10px; font-size: 1.1rem; font-weight: 900; text-decoration: none; box-shadow: 0 6px 24px rgba(255,107,0,0.45); transition: transform 0.15s, box-shadow 0.15s; cursor: pointer; border: none; }
    .hero-cta:hover { transform: translateY(-2px); box-shadow: 0 10px 30px rgba(255,107,0,0.55); }

    .product-section { max-width: 1100px; margin: 0 auto; padding: 50px 20px; display: grid; grid-template-columns: 1fr 1fr; gap: 50px; align-items: start; }
    @media (max-width: 768px) { .product-section { grid-template-columns: 1fr; gap: 30px; } }

    .gallery-wrap { position: sticky; top: 20px; }
    .main-img-wrap { width: 100%; aspect-ratio: 1/1; border-radius: 16px; overflow: hidden; background: white; box-shadow: 0 8px 32px rgba(0,0,0,0.12); margin-bottom: 12px; }
    .main-img-wrap img { width: 100%; height: 100%; object-fit: cover; }
    .thumbs-row { display: flex; gap: 8px; flex-wrap: wrap; }
    .thumb { width: 72px; height: 72px; border-radius: 8px; overflow: hidden; cursor: pointer; border: 2px solid transparent; transition: border-color 0.15s; background: white; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
    .thumb.active, .thumb:hover { border-color: var(--orange); }
    .thumb img { width: 100%; height: 100%; object-fit: cover; }
    .img-placeholder { width: 100%; aspect-ratio: 1/1; background: #f0f0f0; border-radius: 16px; display: flex; align-items: center; justify-content: center; color: #aaa; font-size: 1rem; }

    .product-info { background: white; border-radius: 20px; padding: 36px; box-shadow: 0 4px 20px rgba(0,0,0,0.06); }
    .product-info h1 { font-size: clamp(1.3rem, 3vw, 1.9rem); font-weight: 900; color: var(--dark); margin-bottom: 20px; line-height: 1.3; }
    .stars { color: #F5A623; font-size: 1.1rem; margin-bottom: 8px; }
    .review-count { font-size: 0.85rem; color: var(--muted); margin-bottom: 20px; }

    .price-block { background: #fff8f3; border: 2px solid #ffd6b0; border-radius: 12px; padding: 20px; margin-bottom: 24px; }
    .price-sale { font-size: 2.6rem; font-weight: 900; color: var(--orange); line-height: 1; }
    .price-orig { font-size: 1rem; text-decoration: line-through; color: var(--muted); margin-top: 4px; }
    .discount-tag { display: inline-block; background: var(--green); color: white; padding: 3px 10px; border-radius: 50px; font-size: 0.8rem; font-weight: 700; margin-right: 8px; }
    .price-per-unit { font-size: 0.85rem; color: var(--muted); margin-top: 6px; }

    .benefits-list { list-style: none; padding: 0; margin-bottom: 24px; }
    .benefits-list li { padding: 8px 0; border-bottom: 1px solid var(--border); font-size: 0.95rem; display: flex; align-items: flex-start; gap: 10px; }
    .benefits-list li:last-child { border-bottom: none; }
    .check { color: var(--green); font-weight: 900; flex-shrink: 0; }

    .paypal-form { display: block; width: 100%; }
    .cta-button { display: block; width: 100%; padding: 18px 24px; background: var(--orange); color: white; font-size: 1.05rem; font-weight: 900; font-family: 'Heebo', sans-serif; border: none; border-radius: 12px; cursor: pointer; box-shadow: 0 6px 20px rgba(255,107,0,0.4); transition: transform 0.15s, box-shadow 0.15s; text-align: center; line-height: 1.3; margin-bottom: 12px; }
    .cta-button:hover { transform: translateY(-2px); box-shadow: 0 10px 28px rgba(255,107,0,0.5); }
    .secure-note { display: flex; align-items: center; justify-content: center; gap: 6px; font-size: 0.82rem; color: var(--muted); }

    .trust-row { display: flex; gap: 12px; flex-wrap: wrap; margin-top: 16px; padding-top: 16px; border-top: 1px solid var(--border); }
    .trust-item { display: flex; align-items: center; gap: 6px; font-size: 0.8rem; color: var(--muted); }

    .section { max-width: 800px; margin: 0 auto; padding: 50px 20px; }
    .section h2 { font-size: clamp(1.3rem, 3.5vw, 1.8rem); font-weight: 900; color: var(--dark); margin-bottom: 24px; display: flex; align-items: center; gap: 12px; }
    .section h2::after { content: ''; flex: 1; height: 2px; background: linear-gradient(to left, transparent, var(--orange)); }

    .steps { list-style: none; padding: 0; counter-reset: step; }
    .steps li { counter-increment: step; padding: 16px 70px 16px 0; position: relative; border-right: 2px solid #f0f0f0; margin-bottom: 4px; }
    .steps li::before { content: counter(step); position: absolute; right: -22px; top: 14px; width: 42px; height: 42px; background: var(--orange); color: white; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 900; font-size: 1.1rem; }

    .for-who-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
    @media (max-width: 500px) { .for-who-grid { grid-template-columns: 1fr; } }
    .for-who-card { background: white; border-radius: 12px; padding: 16px 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.06); display: flex; align-items: flex-start; gap: 12px; font-size: 0.95rem; }
    .for-who-emoji { font-size: 1.5rem; flex-shrink: 0; }

    .safety-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px; }
    .safety-item { background: #f0fff4; border: 1px solid #c6f6d5; border-radius: 10px; padding: 14px 16px; font-size: 0.9rem; display: flex; gap: 10px; align-items: flex-start; }

    .offer-strip { background: linear-gradient(135deg, var(--dark) 0%, #0f3460 100%); color: white; text-align: center; padding: 70px 20px; position: relative; overflow: hidden; }
    .offer-strip::before { content: ''; position: absolute; inset: 0; background: radial-gradient(ellipse at 50% 100%, rgba(255,107,0,0.2) 0%, transparent 60%); }
    .offer-inner { position: relative; z-index: 1; max-width: 600px; margin: 0 auto; }
    .offer-strip h2 { font-size: clamp(1.6rem, 5vw, 2.4rem); font-weight: 900; margin-bottom: 8px; }
    .offer-strip .big-price { font-size: clamp(3rem, 10vw, 5rem); font-weight: 900; color: var(--orange); line-height: 1; margin: 16px 0 8px; }
    .offer-strip .orig-price { font-size: 1.2rem; opacity: 0.6; text-decoration: line-through; margin-bottom: 8px; }
    .offer-strip .sub-price { font-size: 0.9rem; opacity: 0.7; margin-bottom: 28px; }
    .urgency-bar { display: inline-flex; align-items: center; gap: 8px; background: rgba(255,107,0,0.2); border: 1px solid rgba(255,107,0,0.5); color: #ffd6b0; padding: 8px 20px; border-radius: 50px; font-size: 0.9rem; font-weight: 600; margin-bottom: 32px; }
    .offer-cta-wrap { max-width: 480px; margin: 0 auto; }
    .offer-cta-wrap .cta-button { font-size: 1.2rem; padding: 22px 30px; }
    .offer-secure { margin-top: 14px; font-size: 0.82rem; opacity: 0.6; }

    .faq-item { background: white; border-radius: 12px; margin-bottom: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); overflow: hidden; }
    .faq-q { padding: 18px 20px; font-weight: 700; cursor: pointer; display: flex; justify-content: space-between; align-items: center; user-select: none; }
    .faq-q::after { content: '+'; font-size: 1.4rem; color: var(--orange); font-weight: 300; }
    .faq-q.open::after { content: '\\2212'; }
    .faq-a { padding: 0 20px; max-height: 0; overflow: hidden; transition: max-height 0.3s ease, padding 0.3s; color: var(--muted); font-size: 0.95rem; }
    .faq-a.open { max-height: 200px; padding: 0 20px 18px; }

    footer { background: var(--dark); color: rgba(255,255,255,0.4); text-align: center; padding: 30px 20px; font-size: 0.82rem; }
    .product-video { width: 100%; max-width: 600px; border-radius: 12px; margin: 0 auto; display: block; }
    """

    js = """
    function setMain(thumb) {
      document.querySelectorAll(".thumb").forEach(t => t.classList.remove("active"));
      thumb.classList.add("active");
      const m = document.getElementById("mainImg");
      if (m) m.src = thumb.dataset.src;
    }
    document.querySelectorAll(".faq-q").forEach(q => {
      q.addEventListener("click", () => {
        const a = q.nextElementSibling;
        const open = q.classList.contains("open");
        document.querySelectorAll(".faq-q").forEach(x => {
          x.classList.remove("open"); x.nextElementSibling.classList.remove("open");
        });
        if (!open) { q.classList.add("open"); a.classList.add("open"); }
      });
    });
    document.querySelector(".hero-cta")?.addEventListener("click", e => {
      e.preventDefault();
      document.getElementById("offer")?.scrollIntoView({behavior:"smooth"});
    });
    """

    html = f"""<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Heebo:wght@300;400;500;700;900&display=swap" rel="stylesheet">
  <style>{css}</style>
</head>
<body>

<div class="topbar">&#128293; מבצע השקה &middot; משלוח לכל הארץ &middot; 100% שביעות רצון או החזר כספי</div>

<section class="hero">
  <div class="hero-inner">
    <div class="badge-row">
      <span class="badge hot">&#128293; הכי נמכר</span>
      <span class="badge">&#9992;&#65039; משלוח מהיר</span>
      <span class="badge">&#128274; תשלום מאובטח</span>
    </div>
    <h1>{title or "המוצר שהילדים שלכם חיכו לו"}</h1>
    <p class="subtitle">חוויה צבעונית, מבעבעת ומפתיעה &mdash; הילדים לא ירצו לצאת מהאמבט!</p>
    <a href="#offer" class="hero-cta">&#128722; להזמנה עכשיו ב&minus;{int(price_ils)} &#8362;</a>
  </div>
</section>

<div class="product-section">
  <div class="gallery-wrap">
    <div class="main-img-wrap">{main_img_html}</div>
    <div class="thumbs-row">{gallery_html}</div>
  </div>
  <div class="product-info">
    <h1>{title or "מוצר פרמיום לילדים"}</h1>
    <div class="stars">&#9733;&#9733;&#9733;&#9733;&#9733;</div>
    <div class="review-count">+4,498 הזמנות &middot; דירוג 4.8/5</div>
    <div class="price-block">
      <div style="display:flex;align-items:baseline;gap:10px;flex-wrap:wrap;">
        <span class="price-sale">{int(price_ils)} &#8362;</span>
        <span class="discount-tag">חסכון {discount_pct}%</span>
      </div>
      <div class="price-orig">מחיר מקורי: {int(original_price_ils)} &#8362;</div>
      {price_per_line}
    </div>
    {bullets_html}
    {paypal_html}
    <div class="secure-note">&#128274; תשלום מאובטח &middot; PayPal &middot; הגנת קונה מלאה</div>
    <div class="trust-row">
      <div class="trust-item">&#128666; משלוח מהיר</div>
      <div class="trust-item">&#8617;&#65039; החזרה קלה</div>
      <div class="trust-item">&#128172; תמיכה בעברית</div>
    </div>
  </div>
</div>

<section class="section">
  <h2>איך זה עובד</h2>
  <ol class="steps">
    <li>ממלאים את האמבט במים חמימים ברמה שנוחה לילד</li>
    <li>בוחרים ביצת אמבט &mdash; נותנים לילד לזרוק אותה למים</li>
    <li>הביצה מתחילה להתמוסס, להבעבע, לשחרר צבע וריח קליל</li>
    <li>מחכה הפתעה &mdash; צעצוע קטן שצף במים לשחק!</li>
  </ol>
</section>

{video_section}

<div style="background:white;padding:50px 0;">
<section class="section" style="padding-top:0;padding-bottom:0;">
  <h2>למי זה מתאים</h2>
  <div class="for-who-grid">
    <div class="for-who-card"><span class="for-who-emoji">&#128106;</span>הורים שמחפשים מתנה חווייתית לפסח במקום עוד שוקולדים</div>
    <div class="for-who-card"><span class="for-who-emoji">&#128117;</span>סבים וסבתות שמחפשים מתנה מקורית לנכדים</div>
    <div class="for-who-card"><span class="for-who-emoji">&#127881;</span>מסיבת כיתה וגן &mdash; אפשר לחלק ביצה לכל ילד</div>
    <div class="for-who-card"><span class="for-who-emoji">&#128705;</span>כל ילד שחולה על אמבטיות, צבעים והפתעות</div>
  </div>
</section>
</div>

<section class="section">
  <h2>בטיחות</h2>
  <div class="safety-grid">
    <div class="safety-item">&#9888;&#65039; מיועד לגיל 3+</div>
    <div class="safety-item">&#128064; תחת השגחת מבוגר</div>
    <div class="safety-item">&#128683; לא לבלוע</div>
    <div class="safety-item">&#129470;&#65039; לשטוף אחרי האמבט</div>
    <div class="safety-item">&#127807; לבדוק על עור רגיש קודם</div>
    <div class="safety-item">&#9989; חומרים עדינים לעור</div>
  </div>
</section>

<section class="offer-strip" id="offer">
  <div class="offer-inner">
    <h2>הצעה מיוחדת &middot; השקה בישראל</h2>
    <div class="orig-price">{int(original_price_ils)} &#8362;</div>
    <div class="big-price">{int(price_ils)} &#8362;</div>
    <div class="sub-price">{sub_price_txt}חסכון של {savings} &#8362;</div>
    <div class="urgency-bar">&#9203; מלאי מוגבל לתקופת ההשקה</div>
    <div class="offer-cta-wrap">
      {paypal_html}
      <div class="offer-secure">&#128274; PayPal &middot; תשלום מאובטח &middot; הגנת קונה</div>
    </div>
  </div>
</section>

<section class="section">
  <h2>שאלות נפוצות</h2>
  <div class="faq-item"><div class="faq-q">האם זה צובע את האמבט?</div><div class="faq-a">בשימוש רגיל לפי ההוראות, הצבע מתפזר במים ומולך עם הריקון, ולא אמור להשאיר כתמים.</div></div>
  <div class="faq-item"><div class="faq-q">מאיזה גיל מתאים?</div><div class="faq-a">מומלץ מגיל 3 ומעלה, בגלל חלקי הצעצוע הקטנים שנשארים אחרי שהביצה נמסה.</div></div>
  <div class="faq-item"><div class="faq-q">כמה זמן לוקח לביצה להתמוסס?</div><div class="faq-a">בדרך כלל כמה דקות, תלוי בטמפרטורת המים ובכמות המים באמבט.</div></div>
  <div class="faq-item"><div class="faq-q">האם הצעצועים בטוחים?</div><div class="faq-a">הצעצועים קטנים ומיועדים למשחק באמבט תחת השגחה. אין לאפשר הכנסת חלקים לפה.</div></div>
  <div class="faq-item"><div class="faq-q">האם זה מגיע כמארז מתנה?</div><div class="faq-a">כן! המארז מגיע כביצי פסחא צבעוניות &mdash; מושלם לסלסילות פסח, ימי הולדת, והפתעות סוף שבוע.</div></div>
</section>

<footer><p>כל הזכויות שמורות &middot; תשלום מאובטח דרך PayPal</p></footer>

<script>{js}</script>
</body>
</html>"""

    return html


def save_page(html, slug, products_dir="products"):
    out_dir = Path(products_dir) / slug
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "index.html"
    out_file.write_text(html, encoding="utf-8")
    print(f"[page] Saved -> {out_file}")
    return out_file


if __name__ == "__main__":
    import sys
    raw_file = sys.argv[1]
    slug = sys.argv[2]
    price = float(sys.argv[3])
    with open(raw_file) as f:
        data = json.load(f)
    html = generate_page(data, [], "<p>PAYPAL PLACEHOLDER</p>", price)
    save_page(html, slug)
