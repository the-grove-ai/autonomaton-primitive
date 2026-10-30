# V-014 — OOBE Config Annotations

**Repo:** `C:\GitHub\autonomaton-clean\grove-autonomaton-primitive-main`
**Branch:** Create worktree `grove-V-014-oobe-annotations`
**Commit:** `V-014-oobe-annotations`

---

## What

The white paper says "three files and a loop." The reference profile has 15 config items. Each is justified but the simplicity claim must be self-documenting. Make it obvious which files ARE the pattern and which enhance the demo.

## The Three Core Files (per white paper Part VIII)

1. `routing.config` — The Cognitive Router's brain
2. `zones.schema` — The sovereignty guardrail
3. `telemetry/telemetry.jsonl` — The feed-first audit trail

Everything else is Out-of-Box Experience enhancement.

## Tasks

### 1. Create `profiles/reference/config/CONFIG-MANIFEST.md`

```markdown
# Config Manifest — Reference Profile

The Autonomaton Pattern requires three files (White Paper Part VIII):

## Core (required by pattern)
- `routing.config` — Intent-to-handler mapping, tier assignment, Cognitive Router config
- `zones.schema` — Zone governance definitions (Green/Yellow/Red)

## Core output (produced by pattern)
- `telemetry/telemetry.jsonl` — Feed-first audit trail, Flywheel input

## OOBE (Out-of-Box Experience enhancements)
These files enhance the reference demo. They are not required by the pattern.
A minimal Autonomaton needs only the three core files above.

- `kaizen.yaml` — Kaizen prompt options (what to show when Andon fires)
- `clarification.yaml` — Fallback menu options
- `persona.yaml` — Engine personality for LLM responses
- `voice.yaml` — Brand voice configuration
- `ux.yaml` — Tips and display preferences
- `tips.yaml` — Contextual tip definitions
- `models.yaml` — LLM tier-to-model mapping and pricing
- `startup.yaml` — Startup mode selection
- `pattern_cache.yaml` — Ratchet cache (auto-generated)
- `profile.yaml` — Profile metadata and display flags
- `content_config.yaml` — Content generation settings
- `entity_config.yaml` — Entity extraction settings
- `mcp.config` — MCP server and capability definitions
- `cognitive-router/prompts/classify_intent.md` — LLM classification prompt template
```

### 2. Add OOBE annotation to each non-core config file

Add this as the SECOND line (after the existing first comment line) in each non-core YAML/config file:

```yaml
# OOBE: Demo enhancement. Core pattern requires only: routing.config, zones.schema, telemetry.jsonl
```

Files to annotate (all in `profiles/reference/config/`):
- `kaizen.yaml`
- `clarification.yaml`
- `persona.yaml`
- `voice.yaml`
- `ux.yaml`
- `tips.yaml`
- `models.yaml`
- `startup.yaml`
- `profile.yaml`
- `content_config.yaml`
- `entity_config.yaml`
- `mcp.config`

Do NOT annotate: `routing.config`, `zones.schema`, `pattern_cache.yaml` (auto-generated).

### 3. Add core annotation to the two core files

Add this as the SECOND line in `routing.config` and `zones.schema`:

```yaml
# CORE: One of three files required by the Autonomaton Pattern (White Paper Part VIII)
```

## Anti-Requirements

- Do NOT change any behavior
- Do NOT modify any values in any config file
- Do NOT restructure or reorder any file content
- Do NOT rename any files
- Comments only. One line per file plus the manifest.

## Acceptance Test

1. `CONFIG-MANIFEST.md` exists in `profiles/reference/config/`
2. Every non-core config file has the OOBE annotation on line 2
3. `routing.config` and `zones.schema` have the CORE annotation on line 2
4. `pytest` passes — zero behavior change
5. A reviewer can identify the three core files in under 10 seconds
