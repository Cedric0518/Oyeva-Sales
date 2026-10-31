# 0004. Market benchmark: provincial retail from Statistics Canada

- Status: Accepted
- Date: 2026-10-31

## Context

Users want to know whether their sales are moving with the market or against it. Retailers often
sell across categories (a pharmacy sells bread), so asking them to pick a narrow sector would be
wrong for many of them. Numbers found on the web are not comparable from one answer to the next.

## Decision

- One benchmark: the province's retail trade, excluding motor vehicle and parts dealers and
  gasoline stations, from Statistics Canada table 20-10-0056-01 (monthly retail sales by province
  and industry).
- Compare year-over-year growth of the business and of the benchmark on the same months, with the
  unadjusted series.
- Every market answer names the benchmark, the source and the latest month published (the table
  is published about seven weeks after the month ends).
- Web search adds context in words only (label Context). No web number goes into a chart.

## Consequences

- One download to keep fresh, with a dated copy kept in Blob Storage.
- The comparison mixes prices and volumes: if prices rise 3%, sales that grow 3% are flat in
  volume. Answers say so.
- Whether the "excluding vehicles and gasoline" total exists as is for every province must be
  checked; if not, it is computed from the table.

## Options considered

- Let the user pick a sector: a false precision for mixed retailers.
- Numbers from web search: not reproducible and not checkable.
