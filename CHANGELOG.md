# Changelog

## Unreleased

- Add a cached YGOPRODeck card reference for all 42 observed passcodes, with
  current names/texts kept separate from replay evidence and historical rules.

- Native `view-replay` JSON import, source integrity checks and coverage audit.
- Promote the supplied unconcealed JSON export of replay 40753-85958923 to primary
  source; retain the original text and its event numbering as a companion.

- Three-KPI artifact scoring with equal weights for state recreation, semantic
  human-move agreement and independently reviewed rule correctness.
- GPT-6.1 Sol recorded as the selected evaluation target; reviewed agentic cases
  and an actual model performance score remain pending.
- Separate structural harness regression probes with journal replay verification;
  their operation coverage does not contribute to the agentic score.
- README and integration guides distinguish the KPI score from literal response
  agreement and structural coverage.

## 0.1.0 — initial public toolkit

- Offline conversion of copied Duelingbook duel text, individually or in batches.
- Hashed observation bundles with lossless decoded source text and line references.
- Source registry and unreviewed candidates for replay 40753-85958923.
- Reviewed decision execution through the public yugioh-harness player interface.
- Explicit response-agreement scoring with missing responses counted as zero.

There are no approved decision cases yet. Automatic state reconstruction,
strategic grading, provider transports and full-duel win-rate evaluation are not
implemented.
