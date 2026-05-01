"""
paypal_button.py — Generate a PayPal Buy Now button HTML.
Uses static PayPal URL approach (no API key needed).
Seller email: loaded from .env PAYPAL_SELLER_EMAIL
"""

import os
import urllib.parse
from dotenv import load_dotenv

load_dotenv()

PAYPAL_SELLER_EMAIL = os.getenv("PAYPAL_SELLER_EMAIL", "")
PAYPAL_BASE_URL = "https://www.paypal.com/cgi-bin/webscr"


def generate_paypal_button(item_name: str, amount_ils: float, currency: str = "ILS") -> dict:
    """
    Generate a PayPal Buy Now button.

    Args:
        item_name: Product name in Hebrew (shown on PayPal checkout)
        amount_ils: Price in ILS (e.g. 200.0)
        currency: Currency code (default ILS)

    Returns dict with:
        - button_html: Full HTML form/button
        - button_url: Direct URL (for simple link)
    """
    if not PAYPAL_SELLER_EMAIL:
        raise ValueError("PAYPAL_SELLER_EMAIL not set in .env")

    params = {
        "cmd": "_xclick",
        "business": PAYPAL_SELLER_EMAIL,
        "item_name": item_name,
        "amount": f"{amount_ils:.2f}",
        "currency_code": currency,
        "button_subtype": "products",
        "no_note": "1",
        "bn": "PP-BuyNowBF",
        "charset": "UTF-8",
    }

    query_string = urllib.parse.urlencode(params)
    button_url = f"{PAYPAL_BASE_URL}?{query_string}"

    button_html = f"""<form action="{PAYPAL_BASE_URL}" method="post" target="_blank" class="paypal-form">
  <input type="hidden" name="cmd" value="_xclick">
  <input type="hidden" name="business" value="{PAYPAL_SELLER_EMAIL}">
  <input type="hidden" name="item_name" value="{item_name}">
  <input type="hidden" name="amount" value="{amount_ils:.2f}">
  <input type="hidden" name="currency_code" value="{currency}">
  <input type="hidden" name="no_note" value="1">
  <input type="hidden" name="charset" value="UTF-8">
  <button type="submit" class="cta-button">
    🛒 אני רוצה לפנק את הילדים – להזמנה עכשיו ב־{int(amount_ils)} ₪
  </button>
</form>"""

    return {
        "button_html": button_html,
        "button_url": button_url,
        "item_name": item_name,
        "amount": amount_ils,
        "currency": currency,
    }


if __name__ == "__main__":
    result = generate_paypal_button("סט ביצי אמבט מבעבעות לילדים", 200.0)
    print(result["button_url"])
    print(result["button_html"])
