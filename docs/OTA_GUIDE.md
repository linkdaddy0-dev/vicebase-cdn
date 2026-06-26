# Over-The-Air (OTA) Updates Guide

This document describes how the ViceBase Android Companion App parses and applies OTA updates from this CDN.

---

## 📡 Version Verification (`ota/version.json`)

The Android application checks `ota/version.json` at startup.

```json
{
  "databaseVersion": "1.0.0",
  "contentVersion": "1.0.0",
  "appMinimumVersion": "1.0.0",
  "lastUpdated": "2026-06-27T00:00:00Z"
}
```

If `databaseVersion` or `contentVersion` is higher than the app's cached database version, the app triggers a download of the main manifest.

---

## 📋 The Main Manifest (`ota/manifest.json`)

The manifest acts as a dynamic dataset registry:

```json
{
  "contentVersion": "1.0.0",
  "generatedAt": "2026-06-27T01:00:00Z",
  "minimumAppVersion": "1.0.0",
  "datasets": [
    {
      "id": "characters",
      "version": "1.0.0",
      "file": "content/characters/characters.json",
      "checksum": "f3b392a95c80...",
      "records": 2
    }
  ]
}
```

### 📥 Dependency Resolution Algorithm

The Android app processes updates dynamically:
1. Parse the `registry/datasets.json` or `ota/manifest.json` dataset list.
2. Build a directed acyclic graph (DAG) of the datasets using the `dependsOn` lists.
3. Topologically sort the datasets to determine order (e.g. `locations` -> `characters` -> `timeline`).
4. Download datasets sequentially, checking that the SHA-256 hash matches the manifest `checksum` block.
5. Save the records into local SQLite or Room database.
