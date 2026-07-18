#!/usr/bin/env python3
"""
Grimoire ECC (Error-Correcting Compression) Tool
=================================================
Scans a grimoire index for redundant, overlapping, or conflicting spells
and compresses them — merging duplicates, rewriting verbose entries, and
bumping ecc_generation.

License: MIT
Usage:
    python ecc.py --index ./grimoire.md --dry-run
    python ecc.py --index ./grimoire.md --apply
    python ecc.py --index ./grimoire.md --report
"""

import argparse
import re
import sys
from pathlib import Path
from datetime import date


# ---------------------------------------------------------------------------
# Spell parsing
# ---------------------------------------------------------------------------

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
SPELL_BLOCK_RE = re.compile(r"<!-- spell: ([\w-]+) -->\n(.*?)(?=<!-- spell:|$)", re.DOTALL)


def parse_frontmatter(text: str) -> dict:
    """Extract YAML-ish frontmatter fields (no external deps, simple key: value)."""
    fields = {}
    for line in text.strip().splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            fields[k.strip()] = v.strip()
    return fields


def load_spells_from_index(index_path: Path) -> list[dict]:
    """Parse inline spells from a grimoire.md index file."""
    content = index_path.read_text(encoding="utf-8")
    spells = []
    for match in SPELL_BLOCK_RE.finditer(content):
        spell_id = match.group(1)
        body = match.group(2).strip()
        fm_match = FRONTMATTER_RE.match(body)
        meta = parse_frontmatter(fm_match.group(1)) if fm_match else {}
        spells.append({"id": spell_id, "meta": meta, "body": body})
    return spells


# ---------------------------------------------------------------------------
# ECC logic
# ---------------------------------------------------------------------------

def find_redundant_pairs(spells: list[dict]) -> list[tuple]:
    """
    Detect pairs of spells that are candidates for merging.
    Criteria:
      - Same domain AND overlapping triggers
      - Same id prefix (e.g. github-token and github-token-path)
      - One spell's triggers are a subset of another's
    Returns list of (spell_a, spell_b, reason) tuples.
    """
    pairs = []
    for i, a in enumerate(spells):
        for b in spells[i + 1:]:
            reason = None
            # Same domain, overlapping triggers
            if a["meta"].get("domain") == b["meta"].get("domain"):
                ta = set(a["meta"].get("trigger", "").lower().split(","))
                tb = set(b["meta"].get("trigger", "").lower().split(","))
                overlap = ta & tb - {""}
                if overlap:
                    reason = f"overlapping triggers: {overlap}"
            # ID prefix match
            if not reason:
                if a["id"].startswith(b["id"]) or b["id"].startswith(a["id"]):
                    reason = "ID prefix overlap"
            if reason:
                pairs.append((a, b, reason))
    return pairs


def report(spells: list[dict], pairs: list[tuple]) -> None:
    print(f"\n📖 Grimoire ECC Report")
    print(f"   Spells loaded : {len(spells)}")
    print(f"   Merge candidates : {len(pairs)}")
    if not pairs:
        print("   ✅ No redundancy detected. Grimoire is clean.")
        return
    print("\n   Candidates:")
    for a, b, reason in pairs:
        print(f"   • {a['id']} ↔ {b['id']}  ({reason})")
    print("\n   Run with --apply to merge these pairs.")


def merge_pair(a: dict, b: dict) -> dict:
    """
    Merge two spells into one. Keeps the lower-ID as canonical, bumps ecc_generation.
    Concatenates Wrong Approaches sections to preserve all known bad paths.
    """
    # ponytail: naive merge — good enough for bootstrap; smarter NLP merge is a future upgrade
    base = a if a["id"] <= b["id"] else b
    other = b if base is a else a

    merged_body = base["body"]

    # Bump ecc_generation
    gen = int(base["meta"].get("ecc_generation", "0")) + 1
    merged_body = re.sub(r"ecc_generation: \d+", f"ecc_generation: {gen}", merged_body)

    # Update last_corrected
    merged_body = re.sub(r"last_corrected: [\d-]+", f"last_corrected: {date.today().isoformat()}", merged_body)

    # Append other's Wrong Approaches if not already present
    other_wrong = re.search(r"## ❌ Known Wrong Approaches\n(.*?)(?=##|$)", other["body"], re.DOTALL)
    if other_wrong:
        extra = other_wrong.group(1).strip()
        # Only append lines not already in base
        existing = merged_body
        new_lines = [ln for ln in extra.splitlines() if ln.strip() and ln not in existing]
        if new_lines:
            merged_body = re.sub(
                r"(## ❌ Known Wrong Approaches\n)",
                r"\1" + "\n".join(new_lines) + "\n",
                merged_body,
                count=1
            )

    # Add ECC history note
    history_note = f"<!-- gen {gen}: merged {other['id']} into {base['id']} -->"
    merged_body += f"\n\n## ECC History\n{history_note}\n"

    return {"id": base["id"], "meta": base["meta"], "body": merged_body, "replaces": other["id"]}


def apply_ecc(index_path: Path, spells: list[dict], pairs: list[tuple]) -> None:
    """Apply merges and rewrite the index file."""
    merged_ids = set()
    new_spells = list(spells)

    for a, b, reason in pairs:
        if a["id"] in merged_ids or b["id"] in merged_ids:
            continue  # already consumed
        merged = merge_pair(a, b)
        new_spells = [s for s in new_spells if s["id"] not in (a["id"], b["id"])]
        new_spells.append(merged)
        merged_ids.add(b["id"] if merged["id"] == a["id"] else a["id"])
        print(f"   ✅ Merged {a['id']} ↔ {b['id']} → {merged['id']} (gen {merged['meta'].get('ecc_generation', '?')})")

    # Rebuild index file — preserve header, replace spells section
    content = index_path.read_text(encoding="utf-8")
    # Update spell count in header
    content = re.sub(r"\*\*Spells:\*\* \d+", f"**Spells:** {len(new_spells)}", content)
    content = re.sub(r"\*\*Last ECC pass:\*\* .*", f"**Last ECC pass:** {date.today().isoformat()}", content)

    # Rebuild index table
    table_rows = "\n".join(
        f"| {s['id']} | {s['meta'].get('domain', '')} | {s['meta'].get('severity', '')} | {s['meta'].get('trigger', '')} |"
        for s in sorted(new_spells, key=lambda x: x["id"])
    )
    table = f"| ID | Domain | Severity | Triggers |\n|----|--------|----------|----------|\n{table_rows}"
    content = re.sub(r"\| ID \|.*?\n\n", table + "\n\n", content, flags=re.DOTALL)

    # Rebuild spells section
    spells_section = "\n\n".join(
        f"<!-- spell: {s['id']} -->\n{s['body']}" for s in sorted(new_spells, key=lambda x: x["id"])
    )
    content = re.sub(r"## Spells\n.*$", f"## Spells\n\n{spells_section}", content, flags=re.DOTALL)

    index_path.write_text(content, encoding="utf-8")
    print(f"\n   📝 Index updated: {index_path}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Grimoire ECC compression tool")
    parser.add_argument("--index", required=True, help="Path to grimoire.md index file")
    parser.add_argument("--dry-run", action="store_true", help="Report only, do not modify")
    parser.add_argument("--apply", action="store_true", help="Apply ECC merges")
    parser.add_argument("--report", action="store_true", help="Report only (same as --dry-run)")
    args = parser.parse_args()

    index_path = Path(args.index)
    if not index_path.exists():
        print(f"❌ Index file not found: {index_path}", file=sys.stderr)
        sys.exit(1)

    spells = load_spells_from_index(index_path)
    pairs = find_redundant_pairs(spells)

    if args.apply and not args.dry_run and not args.report:
        apply_ecc(index_path, spells, pairs)
    else:
        report(spells, pairs)


if __name__ == "__main__":
    main()
