"""
Grimoire Bootstrap — scan agent skills directory and draft spells from Pitfalls sections.
Outputs spell drafts to stdout for human review. Does NOT auto-push anything.

Usage:
    python3 tools/bootstrap.py --skills-dir /path/to/skills --out-dir ./spells-draft

Review all output before committing to the repo.
"""
import argparse, re, sys
from pathlib import Path

PITFALL_HEADERS = re.compile(
    r'^#+\s*(pitfall|known.wrong|wrong.approach|caveat|gotcha|common.mistake)',
    re.IGNORECASE | re.MULTILINE
)

def extract_bullets(text: str) -> list[str]:
    bullets = []
    for line in text.splitlines():
        m = re.match(r'^\s*[-*]\s+(.+)', line)
        if m:
            bullets.append(m.group(1).strip())
    return bullets

def slug(name: str) -> str:
    return re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')

def draft_spell(skill_name: str, domain: str, bullets: list[str]) -> str:
    triggers = [skill_name.replace('-', ' ')]
    sep = "\n  - "
    return f"""---
id: {slug(domain)}-{slug(skill_name)}
version: 1.0.0
domain: {domain}
trigger:
  - {sep.join(triggers)}
severity: warning
origin: auto
ecc_generation: 0
last_corrected: # TODO: fill in date
tags:
  - {skill_name}
---

## ✅ Correct Action

*(TODO: fill in the correct action for {skill_name})*

## ❌ Known Wrong Approaches

{chr(10).join('- ' + b for b in bullets[:6])}

## Why

*(TODO: explain why)*

## ECC History

<!-- gen 0: auto-extracted from skill pitfalls -->
"""

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--skills-dir', required=True)
    parser.add_argument('--out-dir', default='./spells-draft')
    args = parser.parse_args()

    skills_dir = Path(args.skills_dir)
    out_dir = Path(args.out_dir)

    skill_files = list(skills_dir.rglob('SKILL.md'))
    print(f"Found {len(skill_files)} skills", file=sys.stderr)

    drafted = 0
    for skill_file in skill_files:
        text = skill_file.read_text(encoding='utf-8', errors='ignore')

        # Get skill name from directory
        skill_name = skill_file.parent.name

        # Get domain from category (grandparent dir if nested, else 'general')
        parts = skill_file.parts
        domain = parts[-3] if len(parts) >= 3 else 'general'

        # Find pitfalls section
        m = PITFALL_HEADERS.search(text)
        if not m:
            continue

        pitfall_text = text[m.start():]
        # Grab until next header
        next_header = re.search(r'^#+\s+\w', pitfall_text[1:], re.MULTILINE)
        if next_header:
            pitfall_text = pitfall_text[:next_header.start() + 1]

        bullets = extract_bullets(pitfall_text)
        if not bullets:
            continue

        spell = draft_spell(skill_name, domain, bullets)
        out_path = out_dir / f"{slug(domain)}-{slug(skill_name)}.md"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(spell, encoding='utf-8')
        print(f"  drafted: {out_path.name}", file=sys.stderr)
        drafted += 1

    print(f"\nDrafted {drafted} spells → {out_dir}", file=sys.stderr)
    print(f"Review all files before committing to the repo.", file=sys.stderr)

if __name__ == '__main__':
    main()
