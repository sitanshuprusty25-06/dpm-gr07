"""Presentation-only card art; no personal card data or financial calculations."""
import html
import json
from pathlib import Path

IMAGES=json.loads((Path(__file__).parent/"assets"/"card_images.json").read_text(encoding="utf-8"))

def card_art(card, compact=False):
    info=IMAGES.get(card["id"],{})
    name=html.escape(card["name"])
    issuer=html.escape(card["issuer"])
    domain=html.escape(card.get("issuer_domain",""))
    hue=html.escape(card["hue"])
    url=html.escape(info.get("url",""),quote=True)
    fallback=(f'<div class="fin-fallback" style="--card-color:{hue}">'
              f'<span>{issuer}</span><span class="fin-chip"></span>'
              f'<strong>{name}</strong><small>Illustrative card</small></div>')
    # Image is an overlay on the illustration. A broken URL leaves a visible fallback.
    photo=(f'<img class="fin-photo" src="{url}" alt="{name} product image" loading="lazy" referrerpolicy="no-referrer" '
           'onerror="this.style.display=\'none\'">' if url else "")
    # Issuer-site icons (not full wordmark). Plain issuer text always remains visible.
    icon=(f'<img class="fin-issuer-icon" src="https://www.google.com/s2/favicons?domain={domain}&amp;sz=64" '
          f'alt="" loading="lazy" referrerpolicy="no-referrer" onerror="this.style.display=\'none\'">' if domain else "")
    return (f'<div class="fin-visual {"compact" if compact else ""}">'
            f'<div class="fin-art">{fallback}{photo}</div>'
            f'<div class="fin-issuer">{icon}<span>{issuer}</span></div></div>')
