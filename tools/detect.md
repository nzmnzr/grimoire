# 🔍 Grimoire Auto-Detection Skill

**Purpose:** Scan an agent's existing skills directory and generate a starter grimoire index.  
**Agent-agnostic:** Works with any agent that has a skills directory of markdown files.  
**License:** MIT

---

## What This Does

This skill instructs an agent to:
1. Scan its local skills directory
2. Read each skill's frontmatter and content
3. Identify existing "correct actions", pitfalls, and known-wrong-approaches
4. Generate spell entries in Grimoire format (see SPEC.md)
5. Build a `grimoire.md` index from the results

This is a **one-time bootstrap** — run it once to seed your Grimoire from existing knowledge. After that, spells are maintained incrementally.

---

## Instructions (give these to your agent)

```
Load all skills from your skills directory.
For each skill:
  1. Read the skill's content — focus on "Pitfalls", "Known issues", "Wrong approaches", "Critical" sections
  2. For each distinct correct-vs-wrong pattern found, draft a spell in Grimoire format (see SPEC.md)
  3. Set origin: auto, ecc_generation: 0, severity based on impact
  4. Set triggers from the skill's tags, name, and trigger keywords in the content

After scanning all skills:
  1. Deduplicate — if two skills produce overlapping spells, merge them (ECC gen 1)
  2. Write each spell as a separate .md file into a /spells/ directory
  3. Build a grimoire.md index table from all spells
  4. Report: how many skills scanned, how many spells generated, any merges performed
```

---

## Agent-Specific Notes

### Hermes Agent
Skills live at `~/.hermes/profiles/<profile>/skills/`. Use `skills_list()` to enumerate, then `skill_view(name)` to read each one. Write output spells alongside your existing skill files or to a dedicated `~/grimoire/spells/` directory.

### Claude (via Projects / system prompt)
Upload your skills as project files. Instruct Claude to read each file and follow the detection instructions above. Download the generated spells.

### GPT / ChatGPT
Paste skill contents into the conversation in batches. Request spell output in Grimoire format. Assemble manually.

### Cursor / Windsurf / Copilot
Open your skills directory as workspace context. Run the detection prompt in chat mode. Output spells to a `/grimoire/` folder in your repo.

---

## Output

After running detection, you should have:

```
grimoire/
├── grimoire.md          ← updated index
└── spells/
    ├── <domain>/
    │   ├── <spell-id>.md
    │   └── ...
    └── ...
```

---

## ECC Pass After Detection

After auto-detection, run `tools/ecc.py` to compress any redundant spells before committing.

```bash
python tools/ecc.py --index ./grimoire.md --dry-run   # preview merges
python tools/ecc.py --index ./grimoire.md --apply      # apply merges
```
