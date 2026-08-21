# Interview resume contract examples

This bundle demonstrates the candidate/ledger boundary for a resumed runtime attempt.
The canonical files are durable AIDD documents. The other files are raw candidates and
must not be copied into the ledger without the merge decision described in the interview
document contracts.

| Example | Expected disposition |
| --- | --- |
| `canonical-questions.md` and `canonical-answers.md` | Accepted canonical ledger |
| `safe-candidate.md` | Normalize presentation only, then accept if required meaning is unchanged |
| `duplicate-candidate.md` | Reject with `duplicate-id`; retain raw evidence |
| `ambiguous-candidate.md` | Stop in explicit `operator-attention`; retain raw evidence |
| `omitted-candidate.md` | Merge by `QID` while preserving the omitted `Q2` question and answer |

No example permits matching by similar prose, inventing an answer, or erasing an omitted
unresolved entry. The safe candidate is intentionally not canonical Markdown: its
normalization belongs to the candidate-ingestion task.
