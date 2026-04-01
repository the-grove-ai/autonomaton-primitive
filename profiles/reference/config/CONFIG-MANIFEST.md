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
