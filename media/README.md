# Media Assets Specifications

This directory contains media configurations, assets maps, and placeholders for the ViceBase Android Companion application.

> [!CAUTION]
> **NO COPYRIGHTED ASSETS**: Do not upload copyrighted screenshots, trailer captures, promotional artwork, or game files. Use only custom layout assets or verified placeholders.

---

## 📐 Image Asset Dimensions & Standards

All images must be compressed to **WebP** format and stay under **300 KB** to optimize load speed and bandwidth consumption.

| Asset Type | Dimension / Resolution | Ideal Aspect Ratio | Max File Size | Target Directory |
| :--- | :--- | :--- | :--- | :--- |
| **Thumbnail** | 512px width | 1:1 (Square) | 50 KB | `media/<type>/<slug>/thumb.webp` |
| **Card Image** | 720px width | 16:9 or 4:3 | 120 KB | `media/<type>/<slug>/card.webp` |
| **Hero/Banner** | 1440px width | 16:9 | 300 KB | `media/<type>/<slug>/hero.webp` |
| **Gallery Items**| 1280px width | Variable | 200 KB | `media/<type>/<slug>/gallery/*.webp` |

---

## 📁 Directory Structure for Assets

Every individual item folder within `media/characters/`, `media/vehicles/`, `media/weapons/`, etc. must adhere to this template:

```text
media/<category>/<item_slug>/
├── metadata.json       # Self-describing links to files
├── thumb.webp          # Square profile or preview image
├── card.webp           # Rectangular banner used in list items
├── hero.webp           # Full size background banner
└── gallery/            # (Optional) Subfolder for additional detail images
    ├── 1.webp
    └── 2.webp
```

---

## 🎨 Asset Categories

- **characters/**: High-quality portraits of protagonists, antagonists, and supporting cast.
- **vehicles/**: Photos or drawings of official, confirmed car models.
- **weapons/**: Weapons icons and illustrations.
- **locations/**: Landscape and skyline banners.
- **logos/**: Brand, manufacturer, and game logo files.
- **icons/**: UI vectors and icons.
- **placeholders/**: Fallback loading graphics.
- **trailers/**: Video thumbnails and promotional link graphics.
