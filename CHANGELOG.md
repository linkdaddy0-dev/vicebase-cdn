# Changelog

All notable changes to the ViceBase OTA database and assets will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to Semantic Versioning.

## [7.1.0] - 2026-10-13

### Added
- News: An Extended Look out now (Aug 27, links straight to the YouTube video),
  GTA VI: The Album (Sep 17), The Goodtime State – Vice City Collection
  collector's box (Sep 24), GTA VI Collection at the Rockstar Store (Oct 8),
  and the six in-game radio stations plus podcasts (Oct 8). News 13 → 18.
- Timeline: The Album announced (Sep 17) and radio stations revealed (Oct 8).
  Timeline 9 → 11.

### Changed
- "The Sound of Leonida" roundup now covers the confirmed radio stations and
  album singles instead of calling the soundtrack unannounced.
- Launch-day timeline entry notes the album and collector's box arrive Nov 19.
- `ota/manifest.json` and `ota/version.json` bumped to 7.1.0; news and timeline
  datasets at 2.2.0 with regenerated SHA-256 checksums.

## [7.0.0] - 2026-08-25

### Added
- Characters: Lori Heder and DWNPLY (named in official site bios; no official
  artwork exists, so branded placeholder cards ship under
  `media/characters/{lori_heder,dwnply}/card.webp`).
- News: An Extended Look premiere (Aug 27), November 19 date reaffirmed,
  physical editions / preload details, official PS5 feature list, and a
  trailer-confirmed music roundup.
- Timeline: full milestone history through the August 27 premiere (2 → 9 entries).

### Changed
- All six datasets under `content/` synced to match the app's bundled data
  exactly (characters 12 → 14, news 5 → 13); richer official bios throughout.
- `ota/manifest.json` and `ota/version.json` bumped to 7.0.0 with regenerated
  SHA-256 checksums. Verified OTA-applied on a real device.

## [1.0.0] - 2026-06-27

### Added
- Master dataset registry (`registry/datasets.json`) specifying initial datasets.
- Schema definitions for characters, vehicles, weapons, locations, timeline, and news.
- Official initial datasets under `content/` containing verified GTA 6 information.
- Setup of empty structured placeholder directories under `media/` with descriptive metadata guides.
- Automated verification script `scripts/validate.js` compiling manifestations and search indexes.
- GitHub Actions workflow for automated repository validations.
