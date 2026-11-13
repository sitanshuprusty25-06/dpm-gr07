# Visual references — current MVP

The Supported cards page uses public product artwork solely for identification. Card and bank marks belong to their owners; the academic prototype is independent and not bank-affiliated. `card_images.json` records the reference image URLs and provenance for all ten products. The UI displays issuer-term links; artwork provenance remains in the repository.

- Amazon Pay ICICI: card-specific reference image from Refpo.
- Swiggy ORNGE: issuer product-page artwork.
- YES BANK Klick (Kiwi): green Kiwi RuPay promotional artwork from the supplied application-page screenshot, stored locally as `kiwi-green-reference.webp`. This is branding artwork, not proof of a physical card or issuer-specific design. No blue issuer-guide image fallback.
- Scapia Federal Visa: standalone orange Visa image from Paisabazaar; no paired-image fallback.
- Scapia Federal RuPay: official paired Scapia artwork, with the green RuPay identified by a short caption inside the image slot. Not a standalone RuPay photo.
- Other cards: individual public reference images recorded in the register. Issuer icons are public website favicon references, not necessarily complete bank logos.

The app fetches and decodes static images server-side, normalizes them without stretching and embeds them as PNG data URIs. Missing or invalid artwork falls back to an explicitly labelled illustration. Only public reference assets are cached; customer selections and transaction data are not cached.

All catalogue art slots are bounded to 280 CSS pixels and use a 1.65 aspect ratio; portrait artwork stays portrait. Issuer, card name, reward and fee sections have consistent minimum heights on desktop. The neutral image mat is shared by light and dark modes. Compare does not fetch catalogue images. There is no separate Home page.

Image host availability and live rendering are not guaranteed. Verify permissions before redistribution beyond the academic demo. No user card photos or private card numbers are collected.
