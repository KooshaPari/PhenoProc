# CLAUDE.md — PhenoProc

Extends parent governance. See the following for canonical definitions:
- **Global baseline:** Refer to global `CLAUDE.md` configuration
- **Phenotype root:** Refer to parent Phenotype organization `CLAUDE.md`
- **AgilePlus mandate:** Refer to AgilePlus repository
- **Governance reference:** `AGENTS.md` (local, this repository)

## Project Overview

- **Name:** PhenoProc
- **Description:** Process management
- **Language Stack:** Rust
- **Status:** Active

## AgilePlus Mandate

All work MUST be tracked in AgilePlus:
- Check for existing specs before implementing
- Create spec for new work: `agileplus specify --title "<feature>" --description "<desc>"`
- No code without corresponding AgilePlus spec

## Quality Checks

From this repository root:
```bash
# Linting and formatting (adjust for project language)
cargo clippy --workspace -- -D warnings
cargo fmt --check

# Testing
cargo test --workspace

# Documentation validation
vale docs/
```

## Worktree & Git Discipline

- Feature work uses repo-specific worktrees: `repos/[PROJECT]-wtrees/<topic>/`
- Canonical repo stays on `main` except during explicit merge operations
- All feature branches are temporary; integrate via pull request or squash commit
- See parent governance for non-destructive change protocol

## Cross-Project Reuse

During development, proactively identify code that is sharable across Phenotype repositories. Prefer extraction into existing shared modules; propose new shared packages when appropriate.

## Related Documents

- `AGENTS.md` — Local agent contract and operating loop
- `FUNCTIONAL_REQUIREMENTS.md` — Functional requirements and test traceability (if present)
- `docs/worklogs/README.md` — Work audit and decision log
- Parent `README.md` — Project-specific documentation

---

For CI, scripting language hierarchy, and other policies, see the canonical sources listed above.
