# 0010. Missing data is not zero

- Status: Accepted
- Date: 2026-11-04

## Context

Sales files have holes: a store closed for a month, an export that misses a month, a file that
starts in September. In Atlas, the online store has no row for July 2025. Statistics Canada has
holes too: the latest months are not published yet, and some values are never published (in the
release of 2026-10-23, the August 2026 benchmark cannot be computed for the Northwest Territories
and Nunavut).

Counting a hole as zero sales gives numbers that look exact and are wrong. On Atlas, the growth
of 2026 (January to December) against 2025 is -35.26% with the empty months counted as zero, and
+5.06% on the months that have sales in both years. The online store's growth from January to
August 2026 is +69.06% with July 2025 counted as zero, and +46.67% without July.

## Decision

A month without data is a hole, never a zero.

- In a chart, a period without any row is `null` (contract version 2).
- A comparison of two periods (`sales_growth`, `target_attainment`, `market_comparison`) uses only
  the months present on both sides. The months left out are named in the answer, and the figure
  on all months is given next to it when it can be computed.
- `market_comparison` stops at the latest month Statistics Canada has published and names the
  later months. It refuses when a benchmark value it needs is not published.

## Consequences

- The numbers can be explained, and they do not jump because an export missed a month.
- Answers are longer: the agent must say which months were left out (instructions, step B4).
- The Atlas oracle (`answers.json`) counts missing months as zero in two places (growth by store,
  target attainment). The tests say where, with a comment.
- A month with only a few rows (a partial export) is not seen as a hole. The data report does not
  flag it yet.

## Options considered

- Count holes as zero: what a spreadsheet does by default, and wrong (the Atlas figures above).
- Fill holes with an estimate: it invents sales.
- Refuse any comparison that meets a hole: too strict, since most real files have one somewhere.
