# 📖 Grimoire

> *Grimoires always choose their Users.*

A self-correcting, agent-agnostic spell registry. Grimoire is a canonical index of proven correct actions — it sits above your agent's skills and ensures mistakes compound into corrections, not repetitions.

---

## What is Grimoire?

Your AI agent has skills. It has memory. But it still makes the same mistakes — wrong SSH flags, stale credentials, deprecated patterns. Every time you correct it, that correction lives in a chat log and disappears next session.

**Grimoire captures corrections as spells** — structured, versioned, ECC-compressed entries that any agent can load and follow.

- 🧠 **Agent-agnostic** — works with Hermes, Claude, GPT, Cursor, any LLM that reads markdown
- 🔁 **Self-correcting** — spells are revised as new mistakes are caught
- ⚡ **ECC compression** — redundant corrections are merged so context stays clean
- 🔌 **Plug-and-play** — one file to load, `grimoire.md`, gives the agent the full index

---

## How It Works

```
Agent makes a mistake
       ↓
User (or agent) captures correction as a spell
       ↓
Spell added to grimoire.md index
       ↓
Next session: agent loads grimoire.md → knows the correct action
       ↓
Over time: ECC pass compresses redundant spells → stays lean
```

---

## Spell Origins

Every spell has one of two origins:

| Origin | Meaning |
|--------|---------|
| `auto` | Agent detected its own wrong action and self-generated the spell |
| `manual` | User explicitly instructed: *"turn that into a spell"* |

Both produce identical spell format. Origin is metadata only.

---

## Repository Structure

```
grimoire/
├── README.md          # This file
├── LICENSE            # MIT
├── SPEC.md            # Spell format specification
├── grimoire.md        # Agent-loadable index (single entry point)
└── tools/
    ├── detect.md      # Auto-detection skill: scan agent's skills → build index
    └── ecc.py         # ECC compression script: merge redundant spells
```

**What is NOT in this repo:**
- Your actual spells — those live in your agent's local environment
- Your credentials, IPs, or personal config
- Any agent-specific skill files

Grimoire is the grammar and the wand. Your spells are yours.

---

## Quick Start

### 1. Load the index
Tell your agent to load `grimoire.md` at the start of each session. For Hermes users, this means adding it as a skill or referencing it in your system prompt.

### 2. Create your first spell
When your agent does something wrong, say:
> *"Turn that correction into a spell."*

The agent generates a `.md` file using the format in `SPEC.md` and adds it to your local grimoire index.

### 3. Run ECC periodically
When spells accumulate, run `tools/ecc.py` to compress redundant entries.

```bash
python tools/ecc.py --index ./my-grimoire.md --dry-run
python tools/ecc.py --index ./my-grimoire.md --apply
```

---

## License

MIT — use it, fork it, build on it. No restrictions.
