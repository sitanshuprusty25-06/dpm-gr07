"""Public reference images and local fallback illustrations; no user card data."""
import base64
import html
import io
import json
from pathlib import Path
from urllib.request import Request, urlopen

import streamlit as st
from PIL import Image


def _encode_image(image):
    """Normalize images while keeping their original aspect ratio."""
    image.thumbnail((720,450))
    out=io.BytesIO()
    image.convert("RGBA").save(out,format="PNG",optimize=True)
    return "data:image/png;base64,"+base64.b64encode(out.getvalue()).decode("ascii")

IMAGES=json.loads((Path(__file__).parent/"assets"/"card_images.json").read_text(encoding="utf-8"))

@st.cache_data(ttl=3600, show_spinner=False, max_entries=24)
def image_data_uri(url):
    """Fetch only static catalogue assets; return nothing for inaccessible/invalid files."""
    if not url or not url.startswith("https://"):
        return ""
    try:
        req=Request(url,headers={"User-Agent":"Mozilla/5.0","Accept":"image/*"})
        with urlopen(req,timeout=3) as response:
            raw=response.read(4_000_001)
        if len(raw)>4_000_000:
            return ""
        with Image.open(io.BytesIO(raw)) as image:
            return _encode_image(image)
    except Exception:
        return ""

def card_art(card, compact=False):
    info=IMAGES.get(card["id"],{})
    name=html.escape(card["name"])
    issuer=html.escape(card["issuer"])
    domain=html.escape(card.get("issuer_domain",""))
    hue=html.escape(info.get("fallback_gradient",card["hue"]),quote=True)
    fallback=(f'<div class="fin-fallback" style="--card-color:{hue}">'
              f'<span>{issuer}</span><span class="fin-chip"></span>'
              f'<strong>{name}</strong><small>Illustrative card</small></div>')
    # Only emit an image after successful decoding. No inline JavaScript event handlers.
    uri=""
    if info.get("local_path"):
        try:
            root=Path(__file__).resolve().parent
            local=(root/info["local_path"]).resolve()
            if local.is_relative_to(root/"assets"):
                with Image.open(local) as image:
                    uri=_encode_image(image)
        except (OSError, ValueError):
            pass
    if not uri:
        for url in [info.get("url","")]+info.get("alternate_urls",[]):
            uri=image_data_uri(url)
            if uri:
                break
    alt=html.escape(info.get("image_alt",card["name"]+" product image"),quote=True)
    photo=(f'<img class="fin-photo" src="{uri}" alt="{alt}">' if uri else "")
    icon=(f'<img class="fin-issuer-icon" src="https://www.google.com/s2/favicons?domain={domain}&amp;sz=64" '
          'alt="" loading="lazy" referrerpolicy="no-referrer">' if domain else "")
    size_class="compact" if compact else ""
    note=info.get("image_caption","") if uri else ""
    caption=f'<div class="fin-art-note">{html.escape(note)}</div>' if note else ""
    art_class="fin-art has-note" if note else "fin-art"
    return (f'<div class="fin-visual {size_class}">'
            f'<div class="{art_class}">{fallback}{photo}{caption}</div>'
            f'<div class="fin-issuer">{icon}<span>{issuer}</span></div></div>')

def library_card(card, summary, fee_text):
    """Consistent, bounded visual, identity, benefits and metadata zones."""
    name=html.escape(card["name"])
    benefit=html.escape(summary)
    fee=html.escape(fee_text)
    form=html.escape(card.get("reward_label","Cashback"))
    return (f'<div class="fin-library-card">{card_art(card)}'
            f'<div class="fin-library-title">{name}</div>'
            f'<div class="fin-library-benefit"><span class="fin-library-label">Reward highlights</span>{benefit}</div>'
            f'<div class="fin-library-meta"><div><span class="fin-library-label">Annual fee</span><strong>{fee}</strong></div>'
            f'<div><span class="fin-library-label">Reward type</span><strong>{form}</strong></div></div></div>')
