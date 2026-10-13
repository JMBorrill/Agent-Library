#!/usr/bin/env python3
"""Record a lawfully obtained source document placed in sources/originals/ (which git ignores).

Writes/updates sources/originals-ledger.json with the file's SHA-256, size, the registry source ID, the
edition/date the reader confirmed on the document, and who registered it. The document itself is never
committed, so restricted texts (ECSS, SRE book, FCA/Basel extracts) are not redistributed. After
registering, update sources/audits/<id>.md with the exact sections verified and set access_status in
sources/registry.json (VERIFIED only for content actually read).

Usage: register_original.py SOURCE_ID FILE --edition "NASA/SP-2016-6105 Rev2" --by "name" [--date YYYY-MM-DD] [--list]
Exit: 0 registered/listed, 2 usage error (unknown source id, file outside sources/originals, missing file).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ORIG = ROOT / "sources" / "originals"
LEDGER = ROOT / "sources" / "originals-ledger.json"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("source_id", nargs="?")
    ap.add_argument("file", nargs="?", type=Path)
    ap.add_argument("--edition")
    ap.add_argument("--by")
    ap.add_argument("--date", default=date.today().isoformat())
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args(argv)
    ledger = json.loads(LEDGER.read_text(encoding="utf-8")) if LEDGER.is_file() else {"documents": []}
    if a.list:
        for d in ledger["documents"]:
            present = (ROOT / d["path"]).is_file()
            ok = present and hashlib.sha256((ROOT / d["path"]).read_bytes()).hexdigest() == d["sha256"]
            print(f"{d['source_id']:<16} {d['edition']:<40} {'present, hash ok' if ok else 'MISSING or CHANGED'}  {d['path']}")
        return 0
    if not (a.source_id and a.file and a.edition and a.by):
        print("need SOURCE_ID FILE --edition --by (or --list)", file=sys.stderr)
        return 2
    ids = {r["id"] for r in json.loads((ROOT / "sources" / "registry.json").read_text(encoding="utf-8"))}
    if a.source_id not in ids:
        print(f"unknown source id {a.source_id}", file=sys.stderr)
        return 2
    f = a.file.resolve()
    if not f.is_file() or ORIG.resolve() not in f.parents:
        print(f"file must exist inside {ORIG.relative_to(ROOT)}/", file=sys.stderr)
        return 2
    entry = {"source_id": a.source_id, "path": f.relative_to(ROOT).as_posix(), "edition": a.edition,
             "sha256": hashlib.sha256(f.read_bytes()).hexdigest(), "bytes": f.stat().st_size,
             "registered_by": a.by, "registered": a.date}
    ledger["documents"] = [d for d in ledger["documents"] if d["path"] != entry["path"]] + [entry]
    LEDGER.write_text(json.dumps(ledger, indent=2) + "\n", encoding="utf-8")
    print(f"registered {entry['path']} for {a.source_id}; now update sources/audits/{a.source_id}.md with verified sections")
    return 0


if __name__ == "__main__":
    sys.exit(main())
