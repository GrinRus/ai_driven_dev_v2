# AGENTS.md

This directory is reserved for shared prompt fragments; current stage packs are self-contained.

## Rules

- Keep shared guidance runtime-agnostic.
- Do not place stage-specific output rules here.
- Do not reintroduce an inactive shared fragment into execution implicitly. Any shared fragment
  must have an explicit consumer, provenance, and regression evidence.
