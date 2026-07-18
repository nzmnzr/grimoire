# 📜 Grimoire Spell Specification

**Version:** 0.1  
**License:** MIT

---

## Overview

A **spell** is a single markdown file with YAML frontmatter. It encodes one proven-correct action and its history of corrections. The format is intentionally minimal — any agent, any language model, any human can read and write it.

---

## Spell File Format

```markdown
---
id: <unique-slug>
version: <semver>
domain: <category>
trigger:
  - <phrase or pattern that activates this spell>
  - <additional trigger>
severity: hint | warning | critical
origin: auto | manual
ecc_generation: <integer>
last_corrected: <YYYY-MM-DD>
tags:
  - <tag>
---

## ✅ Correct Action

<The exact correct thing the agent should do. Be specific. Include exact commands, paths, flags if relevant.>

## ❌ Known Wrong Approaches

- <Wrong approach 1> — <why it fails>
- <Wrong approach 2> — <why it fails>

## Why

<Brief explanation of why the correct action is correct. Context that would help an agent reason about edge cases.>

## ECC History

<!-- ecc_generation 0: original entries before any compression -->
<!-- ecc_generation N: what changed in each pass -->
```

---

## Field Definitions

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique slug. Lowercase, hyphens. e.g. `ssh-host`, `github-token-path` |
| `version` | semver | Spell version. Start at `1.0.0`. Increment patch on ECC rewrites, minor on behavior change. |
| `domain` | string | Category. e.g. `infrastructure`, `credentials`, `trading`, `smart-home` |
| `trigger` | list | Phrases or task types that should activate this spell. Used by auto-detection. |
| `severity` | enum | `hint` = nice to know. `warning` = likely wrong without this. `critical` = agent MUST check before acting. |
| `origin` | enum | `auto` = agent self-generated. `manual` = user instructed. |
| `ecc_generation` | int | How many compression passes this spell has been through. Starts at `0`. |
| `last_corrected` | date | ISO 8601 date of last human-verified correction. |

### Optional Fields

| Field | Type | Description |
|-------|------|-------------|
| `tags` | list | Free-form tags for search and filtering. |
| `expires` | date | ISO 8601. If set, spell is stale after this date and should be reviewed. |
| `source_skill` | string | Name of the agent skill this spell relates to. |
| `replaces` | string | ID of a previous spell this one supersedes (after ECC merge). |

---

## Severity Guide

```
hint     → "FYI, this approach exists"
warning  → "You'll probably do this wrong without reading this"
critical → "Stop. Check this before you act. Mistakes here cause real damage."
```

Use `critical` sparingly. If everything is critical, nothing is.

---

## ECC (Error-Correcting Compression)

ECC is the process of detecting redundancy across spells and compressing them into a single, cleaner spell.

### When to run ECC

- After 3+ corrections to the same domain
- When two spells have overlapping triggers
- When a spell's "Wrong Approaches" list grows beyond 4 items

### ECC Rules

1. **Merge** — two spells about the same action → one spell with combined knowledge
2. **Compress** — verbose explanation → tighter prose that preserves all meaning
3. **Supersede** — old spell replaced by new → mark old with `replaces` pointer, archive or delete
4. **Increment** — bump `ecc_generation` after each pass
5. **Preserve** — never delete a "Why" explanation entirely; compress it, don't drop it

### ECC is NOT

- Deleting corrections because they seem obvious
- Removing "Wrong Approaches" because they're embarrassing
- Shortening a spell so much it loses precision

---

## Example Spell

```markdown
---
id: github-token-path
version: 1.1.0
domain: credentials
trigger:
  - github token
  - github auth
  - GITHUB_TOKEN
  - push to github
severity: critical
origin: manual
ecc_generation: 1
last_corrected: 2026-07-18
tags:
  - github
  - credentials
  - windows
---

## ✅ Correct Action

Read GITHUB_TOKEN from your agent profile's `.env` file.
Token should have full repo scope.

```bash
TOKEN=$(grep GITHUB_TOKEN ~/.agent-profile/.env | cut -d= -f2 | tr -d '\r\n')
```

## ❌ Known Wrong Approaches

- Using a default/system-level credential path — it may hold a limited-scope token that returns 401 on repo operations.
- Hardcoding token in script literals — some sandboxes mask it, arriving as `***`.

## Why

Multiple credential files can exist on a system with different scopes. Always read from the profile-specific path configured for your agent, not the system default.

## ECC History

<!-- gen 0: original entries about token path, token type, and sandbox masking -->
<!-- gen 1: merged into single spell with all facts preserved -->
```

---

## grimoire.md Index Format

The `grimoire.md` file is the single agent-loadable entry point. It is a flat index of all active spells.

```markdown
# Grimoire Index

> Load this file at the start of each session. Check triggers before acting.

## Index

| ID | Domain | Severity | Triggers |
|----|--------|----------|----------|
| github-token-path | credentials | critical | github token, GITHUB_TOKEN, push to github |
| ssh-hostname | infrastructure | critical | ssh hostname, connect to host |
| ... | ... | ... | ... |

---

## Spells

<!-- spell: github-token-path -->
[inline content of spell or link to spell file]

<!-- spell: ssh-hostname -->
[inline content of spell or link to spell file]
```

Agents read the index table first (fast lookup by trigger), then load specific spell bodies as needed.
