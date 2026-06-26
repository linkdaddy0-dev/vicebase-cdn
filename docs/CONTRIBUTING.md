# Contributing Guide

We welcome contributions to the ViceBase companion database! Please follow this workflow to ensure that updates are clean, legally safe, and fully functional.

---

## 🛠️ Step-by-Step Contribution Workflow

1. **Clone & Branch**:
   ```bash
   git clone https://github.com/linkdaddy0-dev/vicebase-cdn.git
   cd vicebase-cdn
   git checkout -b feature/your-content-update
   ```
2. **Add / Edit JSON**:
   Update files in the `content/` folder following the constraints in `docs/JSON_GUIDE.md` and schemas.
3. **Verify Integrity**:
   Run the local validation suite:
   ```bash
   node scripts/validate.js
   ```
   This will validate schemas, check for duplicate IDs, build the master search index, and compile the manifest and version manifests.
4. **Review Diffs**:
   Ensure only expected data has changed. Double-check that no copyrighted images or materials have been added.
5. **Commit & Pull Request**:
   Commit the changes (including the updated `ota/manifest.json`, `ota/version.json` and `search/index.json`) and open a Pull Request.
