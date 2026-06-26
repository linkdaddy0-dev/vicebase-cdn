# Media Specifications Guide

This document describes how to structure and optimize visual assets stored in this CDN.

---

## 🎨 Asset Optimization Workflow

1. **Format**: All images must be converted to **WebP** (`.webp`). No PNG or JPEG files are allowed in production.
2. **File Size Limit**: No image file should exceed **300 KB**. Card images and thumbnails should strive to be under **100 KB**.
3. **Naming Convention**:
   - `thumb.webp`
   - `card.webp`
   - `hero.webp`
   - `gallery/1.webp`, `gallery/2.webp`

---

## 📐 Dimensions

- **Thumbnails (`512x512px`)**: Used in grid views, search results, and list icons. Should focus on the subject.
- **Card Images (`720x405px`)**: Aspect ratio 16:9. Used as backgrounds in catalog items.
- **Hero Images (`1440x810px`)**: Aspect ratio 16:9. High-resolution banners for detail page headers.
- **Gallery Images (`1280x720px`)**: High-res slideshow items.
