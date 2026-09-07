# AGENTS.md

This directory contains deterministic Python regression, integration, architecture, and
packaging tests. Node DOM/state tests live in `frontend/`; browser journeys live separately
in `browser_tests/` and are not included by the default pytest test paths.

## Rules

- Keep tests fast and deterministic.
- Test observable behavior and contract boundaries with real local fixtures. Use scoped fakes
  for external runtimes so routine tests need no provider credentials or network execution.
- Keep subsystem tests focused; use harness scenarios for workflow integration and grading.
  A scenario complements the nearest regression test rather than replacing it.
- Preserve failure, repair, resume, ownership, and evidence assertions when refactoring.
- Follow `docs/agent-development.md` for the relevant Python, Node, and browser check lanes.
