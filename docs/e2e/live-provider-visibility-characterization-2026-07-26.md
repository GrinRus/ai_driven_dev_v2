# Live provider visibility characterization — 2026-07-26

This provider-free record characterizes the process boundary used by the Wave 36
prod-like live-acceptance harness. It is diagnostic evidence for
`W36-E7-S4-T38`, not an isolation claim and not a live-provider result.

## Candidate and method

- Product revision: `7c1792ca2b9dfe17041b930e9a271adad461171e`.
- Launch boundary:
  `aidd.harness.live_e2e_black_box_steps._run_black_box_command`.
- Canary module: `aidd.harness.live_acceptance_visibility`.
- The canary ran with the real AIDD checkout as `source` and disposable
  `target`, `provider`, `credential`, and `sibling-provider` roots.
- Each root contained one known readable sentinel. The canary tested directory
  listing, bounded sentinel reading, and creation plus cleanup of one unique file.
- A synthetic sibling-provider credential environment variable tested inherited
  environment visibility. The report recorded only presence and non-empty state;
  it did not render the value.

The focused provider-free matrix was:

```bash
uv run --extra dev pytest -q \
  tests/harness/test_live_acceptance_visibility.py \
  tests/harness/test_live_acceptance_preflight.py \
  tests/test_live_acceptance_architecture.py
```

Result: `16 passed`.

## Normalized result

| Root class | List | Read | Write |
| --- | --- | --- | --- |
| `source` | allowed | allowed | allowed |
| `target` | allowed | allowed | allowed |
| `provider` | allowed | allowed | allowed |
| `credential` | allowed | allowed | allowed |
| `sibling-provider` | allowed | allowed | allowed |

The synthetic sibling-provider credential environment variable was present and
non-empty inside the launched process. Its value was not included in diagnostics.

The write probes removed their unique canary files before returning success. No
canary residue remained in the source or disposable roots.

## Conclusions

1. The current live command boundary has ambient read and write visibility across
   all characterized filesystem roots.
2. Separate provider directory names do not create a security or isolation
   boundary.
3. The launched process inherits sibling-provider credential environment state
   when the launching environment contains it.
4. `W36-E7-S4-T39` must enforce both an allowlisted environment and a real
   provider-private filesystem boundary for the command and its descendants.
5. The same executable canary is the acceptance probe for `T39`: own target and
   evidence access must remain available while source writes, sibling roots, and
   sibling credentials become unavailable.
