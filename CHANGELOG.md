# Changelog

## Unreleased

- Native `view-replay` JSON is the supported replay input. Remove the text fixture,
  bundle, candidate index and converters, plus exact-response scoring and isolated
  operation probes. Reimport old sources as native JSON and review their positions.
- Document replay acquisition through browser Network/Response inspection.
- Preserve 554 native plays across two games, source integrity and unreviewed
  candidates; candidate indexes now identify native `source_index` values.
- Cache current YGOPRODeck names/texts for all 42 observed passcodes separately
  from original replay evidence and historical rules.
- Record the user’s Perfect Circle 2007 format declaration and a September 2007
  reference; historical card text and legality review remain pending.
- Three equally weighted KPIs: state recreation, semantic human-move agreement
  and independently reviewed rule correctness. Expose `score-kpis` in the CLI.
- GPT-6.1 Sol is the evaluation target; a complete measured model score remains
  pending. Update CI and source packages for the native JSON workflow.

## 0.1.0 — initial public toolkit

- Offline conversion of copied Duelingbook duel text, individually or in batches.
- Hashed observation bundles with lossless decoded source text and line references.
- Source registry and unreviewed candidates for replay 40753-85958923.
- Reviewed decision execution through the public yugioh-harness player interface.
- Explicit response-agreement scoring with missing responses counted as zero.

There are no approved decision cases yet. Automatic state reconstruction,
strategic grading, provider transports and full-duel win-rate evaluation are not
implemented.
