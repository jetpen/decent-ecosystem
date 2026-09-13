# Domain Docs

This is a single-context repository.

## Before exploring, read these

- `CONTEXT.md` at the repository root
- Relevant ADRs under `docs/adr/`

If these files do not exist, proceed silently. Create them lazily when domain terms or architectural decisions are resolved.

## File structure

```text
/
├── CONTEXT.md
├── docs/adr/
└── src/
```

Use terminology defined in `CONTEXT.md` for issue titles, proposals, tests, and other outputs. If a required concept is not defined, note it as a domain-modeling gap.

If an output contradicts an existing ADR, identify the conflict explicitly instead of silently overriding it.
