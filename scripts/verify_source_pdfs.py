#!/usr/bin/env python3
"""Verify pinned source bytes; this does not certify framework compliance."""
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys


def verify(root):
    manifest = json.loads((root / "sources/pdf-manifest.json").read_text())
    errors = []
    seen = set()
    parser = shutil.which("pdfinfo")
    sources = manifest["sources"]
    if not sources:
        errors.append("No bundled sources declared")
    for source in sources:
        sid = source["id"]
        if sid in seen:
            errors.append(f"Duplicate source ID: {sid}")
        seen.add(sid)
        path = (root / source["path"]).resolve()
        if not path.is_relative_to((root / "sources/pdfs").resolve()):
            errors.append(f"{sid}: path outside sources/pdfs")
            continue
        if not path.is_file():
            errors.append(f"{sid}: missing PDF")
            continue
        data = path.read_bytes()
        checks = {
            "PDF signature": data.startswith(b"%PDF-"),
            "byte count": len(data) == source["size_bytes"],
            "SHA-256": hashlib.sha256(data).hexdigest() == source["sha256"],
            "HTTPS provenance": source["download_url"].startswith("https://"),
            "reuse notice": bool(source.get("reuse") and source.get("rights_url")),
        }
        for label, passed in checks.items():
            if not passed:
                errors.append(f"{sid}: {label} failed")
        if parser:
            result = subprocess.run([parser, str(path)], capture_output=True, text=True)
            match = re.search(r"^Pages:\s+(\d+)", result.stdout, re.M)
            if result.returncode or not match or int(match[1]) != source["pages"]:
                errors.append(f"{sid}: PDF parsing/page count failed")
    return errors, len(sources), bool(parser)


def main():
    root = Path(__file__).resolve().parents[1]
    try:
        errors, count, parsed = verify(root)
    except (KeyError, ValueError, OSError, TypeError) as exc:
        print(f"FAIL: invalid or unreadable manifest: {exc}", file=sys.stderr)
        return 1
    for error in errors:
        print(f"FAIL: {error}", file=sys.stderr)
    if errors:
        return 1
    print(f"PASS: {count} pinned PDF files match their provenance and integrity records.")
    print("PASS: PDF parsing and page counts." if parsed else
          "SKIP: PDF parsing/page counts (pdfinfo unavailable); byte checks only.")
    print("This is not engineering, regulatory or professional approval.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
