"""
Grimoire trigger-matching test suite.
Tests that spells fire (or don't) for given intent strings.

Usage:
    python3 tools/test_grimoire.py --spells-dir ./spells
"""
import argparse, re, sys
from pathlib import Path

def load_spells(spells_dir: Path) -> list[dict]:
    spells = []
    for f in spells_dir.rglob("*.md"):
        text = f.read_text(encoding="utf-8")
        m = re.match(r'^---\n(.*?)\n---', text, re.DOTALL)
        if not m:
            continue
        fm = m.group(1)
        t_block = re.search(r'trigger:(.*?)(?=\n\w|\Z)', fm, re.DOTALL)
        triggers = re.findall(r'^\s+-\s+(.+)$', t_block.group(1) if t_block else '', re.MULTILINE)
        sid = re.search(r'^id:\s*(.+)$', fm, re.MULTILINE)
        sev = re.search(r'^severity:\s*(.+)$', fm, re.MULTILINE)
        spells.append({
            "id": sid.group(1).strip() if sid else f.stem,
            "severity": sev.group(1).strip() if sev else "hint",
            "triggers": [t.strip().lower() for t in triggers],
        })
    return spells

def check(intent: str, spells: list[dict]) -> list[dict]:
    il = intent.lower()
    return [sp for sp in spells if any(t in il for t in sp["triggers"])]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--spells-dir', default='./spells')
    args = parser.parse_args()

    spells_dir = Path(args.spells_dir)
    if not spells_dir.exists():
        print(f"No spells directory found at {spells_dir} — nothing to test.")
        sys.exit(0)

    spells = load_spells(spells_dir)
    if not spells:
        print("No spells loaded — add spells first.")
        sys.exit(0)

    print(f"Loaded {len(spells)} spells\n")

    # Example test cases — edit to match your own spells
    scenarios = [
        # (intent string, [expected spell ids that should fire])
        # Add your own based on what spells you've written
    ]

    if not scenarios:
        print("No test scenarios defined. Edit tools/test_grimoire.py to add your own.")
        sys.exit(0)

    passed = failed = 0
    for intent, expected_ids in scenarios:
        hits = check(intent, spells)
        hit_ids = [h["id"] for h in hits]
        missed = [e for e in expected_ids if e not in hit_ids]
        false_pos = hit_ids if not expected_ids and hit_ids else []
        ok = not missed and not false_pos
        passed += ok; failed += not ok
        print(f"{'✅' if ok else '❌'} '{intent[:60]}'")
        fired = ', '.join(f'[{h["severity"]}] {h["id"]}' for h in hits)
        if hits: print(f"   fired: {fired}")
        if missed: print(f"   MISSED: {missed}")
        if false_pos: print(f"   FALSE POS: {false_pos}")

    print(f"\n{'='*60}")
    print(f"Results: {passed}/{len(scenarios)} passed")
    sys.exit(0 if failed == 0 else 1)

if __name__ == '__main__':
    main()
