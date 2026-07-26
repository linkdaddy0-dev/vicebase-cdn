#!/usr/bin/env python3
"""
Regenerate ota/manifest.json checksums from the bytes actually committed to the repo.

Run from the root of the vicebase-cdn repository:

    python regenerate_checksums.py

Why this exists
---------------
Every checksum currently in ota/manifest.json was generated on Windows from CRLF
working-tree copies of the dataset files, while GitHub serves the committed LF bytes.
The digests therefore did not match anything a client could download. Nothing noticed,
because the app parsed the `checksum` field and never verified it.

The app now verifies, with a CRLF-normalization fallback so the current manifest keeps
working. Running this script (and committing a .gitattributes with `*.json text eol=lf`,
which this script writes if absent) makes the manifest match the served bytes, after
which the fallback is no longer exercised.

This reads files in binary mode, so what it hashes is exactly what a client receives.
"""

import hashlib
import json
import os
import sys

MANIFEST_PATH = os.path.join("ota", "manifest.json")
GITATTRIBUTES_PATH = ".gitattributes"
EOL_RULE = "*.json text eol=lf"


def sha256_of(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def count_records(path):
    with open(path, "rb") as handle:
        data = json.load(handle)
    if isinstance(data, dict):
        return len(data.get("items", []))
    if isinstance(data, list):
        return len(data)
    return 0


def ensure_gitattributes():
    existing = ""
    if os.path.exists(GITATTRIBUTES_PATH):
        with open(GITATTRIBUTES_PATH, "r", encoding="utf-8") as handle:
            existing = handle.read()
    if EOL_RULE in existing:
        return False
    with open(GITATTRIBUTES_PATH, "a", encoding="utf-8", newline="\n") as handle:
        if existing and not existing.endswith("\n"):
            handle.write("\n")
        handle.write("# Keep JSON line endings stable so manifest checksums match served bytes.\n")
        handle.write(EOL_RULE + "\n")
    return True


def main():
    if not os.path.exists(MANIFEST_PATH):
        sys.exit(f"{MANIFEST_PATH} not found. Run this from the vicebase-cdn repo root.")

    with open(MANIFEST_PATH, "rb") as handle:
        manifest = json.load(handle)

    changed = 0
    for dataset in manifest.get("datasets", []):
        path = dataset["file"]
        if not os.path.exists(path):
            sys.exit(f"Dataset file missing: {path}")

        actual = sha256_of(path)
        records = count_records(path)

        if dataset.get("checksum") != actual:
            print(f"  {dataset['id']:<12} checksum {dataset.get('checksum', '')[:12]}… -> {actual[:12]}…")
            dataset["checksum"] = actual
            changed += 1
        if dataset.get("records") != records:
            print(f"  {dataset['id']:<12} records  {dataset.get('records')} -> {records}")
            dataset["records"] = records
            changed += 1

    if changed:
        # newline="\n" so this script cannot reintroduce the problem it exists to fix.
        with open(MANIFEST_PATH, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(manifest, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
        print(f"\nUpdated {MANIFEST_PATH} ({changed} field(s) changed).")
    else:
        print("All checksums and record counts already match.")

    if ensure_gitattributes():
        print(f"Added '{EOL_RULE}' to {GITATTRIBUTES_PATH}.")
        print("Run 'git add --renormalize .' so existing files pick up the rule.")


if __name__ == "__main__":
    main()
