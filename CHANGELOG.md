# Changelog

All notable changes to the ViceBase OTA database and assets will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to Semantic Versioning.

## [1.0.0] - 2026-06-27

### Added
- Master dataset registry (`registry/datasets.json`) specifying initial datasets.
- Schema definitions for characters, vehicles, weapons, locations, timeline, and news.
- Official initial datasets under `content/` containing verified GTA 6 information.
- Setup of empty structured placeholder directories under `media/` with descriptive metadata guides.
- Automated verification script `scripts/validate.js` compiling manifestations and search indexes.
- GitHub Actions workflow for automated repository validations.
