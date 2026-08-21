# Invalid task-card presentation fixture

These shapes remain invalid because they hide executable task meaning:

```text
- TL-1: add the contract; TL-2: add tests
```

```text
| Task | Outcome | Verification |
| --- | --- | --- |
| TL-1 | add the contract | run tests |
```

They omit the required H3 card fields, stable task-local acceptance evidence, or explicit
dependency/verification entries. A validator must reject them rather than infer a rich tasklist.
