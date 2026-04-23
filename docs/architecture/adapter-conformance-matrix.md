# Adapter Conformance Matrix

## Purpose

This document defines the maintained-runtime conformance matrix used by harness and CI checks.

It converts adapter-extension safety from distributed expectations into one repeatable matrix.

## Maintained runtimes

- `generic-cli`
- `claude-code`
- `codex`
- `opencode`

## Required conformance dimensions

- `probe_behavior`
- `capability_declaration`
- `raw_log_capture`
- `failure_mapping`
- `question_surfacing`
- `timeout_behavior`
- `workspace_targeting`

## Matrix

| Runtime | probe_behavior | capability_declaration | raw_log_capture | failure_mapping | question_surfacing | timeout_behavior | workspace_targeting |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `generic-cli` | required | required | required | required | required | required | required |
| `claude-code` | required | required | required | required | required | required | required |
| `codex` | required | required | required | required | required | required | required |
| `opencode` | required | required | required | required | required | required | required |

## Usage rule

The matrix is normative for maintained runtimes. Any new maintained runtime must add one new row and must satisfy every required dimension.
