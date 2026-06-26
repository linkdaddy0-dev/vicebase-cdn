# JSON Specifications Guide

All database updates must conform to strict JSON standards and validate against their respective schemas.

---

## 🛠️ Global Metadata Header

Every content JSON file located under `content/<dataset_name>/<dataset_name>.json` must start with a `metadata` header:

```json
{
  "metadata": {
    "dataset": "characters",
    "version": "1.0.0",
    "generatedAt": "2026-06-27T00:00:00Z",
    "language": "en",
    "region": "global",
    "verified": true,
    "source": "Rockstar Games announcements"
  },
  "items": []
}
```

---

## 🔑 Common Item Fields

Every object in the `"items"` array must contain the following fields:

| Field Name | Type | Description |
| :--- | :--- | :--- |
| `id` | String | A stable, snake_case string prefixing the type, e.g., `character_lucia` |
| `slug` | String | URL-friendly name, e.g., `grotti-cheetah` |
| `title` | String | Human readable display title |
| `description`| String | Detailed summary of the entity |
| `status` | String | One of: `"confirmed"`, `"official"`, `"community"`, `"coming_soon"`, `"deprecated"` |
| `tags` | Array | Categorization tags (e.g. `["playable", "protagonist"]`) |
| `relationships`| Object | Lists of associated entity IDs (e.g., `{"locations": ["location_vice_city"]}`) |
| `verified` | Boolean | True if officially verified |
| `source` | String | Name of the source |
| `sourceUrl` | String | Absolute URI link to source |
| `createdAt` | String | Date-Time format (ISO-8601) when added to the repo |
| `updatedAt` | String | Date-Time format (ISO-8601) of last change |
| `verifiedAt` | String | Date-Time format (ISO-8601) of last verification |
| `version` | String | Semantic version string, e.g., `"1.0.0"` |
