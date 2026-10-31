# API contract (frontend and backend)

This file is the single source of truth for what the API sends and what the frontend expects.
Both sides read it. It changes only through a pull request labeled `contract`, and that pull
request updates both sides or opens the issue that will (see `docs/decisions/0007`).

Version: 1 (2026-10-31). Example values are the real values of the Atlas sample data
(`evals/data/atlas/`).

## 1. Conventions

- Base URL: `VITE_API_BASE_URL` on the frontend (for example `http://localhost:8000` locally).
- JSON in UTF-8. Dates in ISO format (`2025-03-01`).
- **Session**: the frontend creates a `session_id` (UUID v4) when the page loads, keeps it in memory
  only, and sends it in the `X-Session-Id` header on every call. Reloading the page starts a new
  session. A missing or invalid header returns `missing_session`.
- **Errors**: HTTP status plus `{"error": {"code": "...", "message": "..."}}`. Codes:
  `unsupported_format`, `file_too_large`, `unreadable_file`, `missing_session`,
  `dataset_not_found`, `rate_limited`, `internal`. The `message` can be shown to the user as is.
- **Limits**: sales file 20 MB; context document 5 MB and 50 pages.

## 2. Provenance values

Every chart, table and explanation carries one of five provenance values.

| Value | Label | Meaning |
|---|---|---|
| `certified` | Certified | Computed by a tested function with a fixed definition. |
| `exploratory` | Exploratory | Computed by code the assistant wrote for this question. |
| `market` | Market | Official statistics (Statistics Canada), fetched by code. |
| `documents` | Your documents | From the document the user uploaded. Not a calculation. |
| `context` | Context | From the web. Not computed from the user's data. |

`documents` and `context` never apply to a chart or a table. The frontend refuses to display a
`chart` or `table` event carrying one of them and logs it as a backend bug.

## 3. `GET /api/health`

`200 {"status": "ok"}`

## 4. Provinces

No route: the list is fixed in the frontend. Codes `ON`, `QC`, `BC`, `AB`, `MB`, `SK`, `NS`, `NB`,
`NL`, `PE`, `YT`, `NT`, `NU`, with their English names; Ontario by default. There is **no sector
choice**: the market benchmark is always the province's retail trade, excluding motor vehicle and
parts dealers and gasoline stations.

## 5. `POST /api/upload`

Request `multipart/form-data`: `file` (required, CSV or XLSX), `region` (required, a province
code), `context` (optional, `.md`, `.pdf` or `.docx`).

Response `200`:

```json
{
  "dataset_id": "ds_3f9a1c2b7d4e8f01",
  "file_name": "atlas_sales.xlsx",
  "sheets": ["Orders", "Targets"],
  "rows": 59764,
  "columns": [
    {"name": "order_id", "type": "text"},
    {"name": "order_date", "type": "date"},
    {"name": "store", "type": "text"},
    {"name": "channel", "type": "text"},
    {"name": "customer", "type": "text"},
    {"name": "customer_type", "type": "text"},
    {"name": "product", "type": "text"},
    {"name": "category", "type": "text"},
    {"name": "quantity", "type": "number"},
    {"name": "unit_price", "type": "number"},
    {"name": "amount", "type": "number"}
  ],
  "roles": {
    "date": "order_date", "amount": "amount", "customer": "customer",
    "product": "product", "quantity": "quantity", "unit_price": "unit_price",
    "region": "store", "order_id": "order_id", "target": "Targets.target"
  },
  "preview": {
    "columns": ["order_id", "order_date", "store", "customer", "product", "quantity", "unit_price", "amount"],
    "rows": [["A0000092", "2024-09-03", "Toronto - Queen Street", "Lakeshore Dental Clinic", "Notebooks, 5 pack", 27, 9.49, 256.23]]
  },
  "checks": [
    {"id": "roles", "name": "Column roles", "status": "ok", "detail": "Date, amount, customer and order columns identified", "amount": null},
    {"id": "duplicates", "name": "Duplicate rows", "status": "warning", "detail": "12 duplicate rows", "amount": 176.83},
    {"id": "amount_mismatch", "name": "Quantity x unit price differs from amount", "status": "warning", "detail": "40 rows", "amount": null},
    {"id": "name_variants", "name": "Same customer written several ways", "status": "warning", "detail": "Lakeshore Dental Clinic appears in 3 spellings", "amount": null},
    {"id": "missing_months", "name": "Months without sales", "status": "warning", "detail": "Online: 2025-07", "amount": null},
    {"id": "dates_out_of_range", "name": "Dates outside the period", "status": "warning", "detail": "2 rows dated 2052", "amount": null},
    {"id": "placeholder_customer", "name": "Placeholder customer", "status": "warning", "detail": "\"Walk-in\" is not a single customer; excluded from customer metrics", "amount": null},
    {"id": "returns", "name": "Returns", "status": "ok", "detail": "805 return lines", "amount": -13190.44}
  ],
  "region": "ON",
  "context": {
    "name": "atlas_context.pdf",
    "format": "pdf",
    "converted": true,
    "tokens": 1100,
    "mode": "full",
    "sections": [
      {"id": "D1", "title": "Atlas General Store: company notes"},
      {"id": "D2", "title": "About the company"},
      {"id": "D3", "title": "Stores and channels"},
      {"id": "D4", "title": "Column dictionary"},
      {"id": "D5", "title": "Customers and loyalty"},
      {"id": "D6", "title": "Store closures"},
      {"id": "D7", "title": "Pricing changes"},
      {"id": "D8", "title": "Promotions"},
      {"id": "D9", "title": "Returns policy"},
      {"id": "D10", "title": "Data notes"}
    ],
    "removed_sections": []
  }
}
```

- A check's `status` is `ok`, `warning` or `error`. `amount` is in dollars, or `null`.
- `roles`: the column the backend recognized for each role, or `null`. If `date` or `amount` is
  `null`, certified metrics refuse to run, and the report says so.
- `context` is `null` when no document was sent. `mode`: `full` (whole document in the
  conversation) or `rag` (search). `tokens` is an estimate.
- `removed_sections`: sections set aside at upload (for example flagged by Prompt Shields), each
  `{"id": "D4", "title": "...", "reason": "..."}`.

## 6. `POST /api/sample`

JSON request `{"sample": "atlas"}`. Same response as `/api/upload` (file `atlas_sales.xlsx`,
document `atlas_context.md`, region `ON`).

## 7. `POST /api/chat` (Server-Sent Events)

JSON request:

```json
{"dataset_id": "ds_3f9a1c2b7d4e8f01", "conversation_id": null, "message": "How much did I sell in 2025?"}
```

`conversation_id` is `null` on the first message, then the one received in the `start` event.
Response: `Content-Type: text/event-stream`, a sequence of `event: <type>` and `data: <json>`
lines, each event followed by a blank line.

| Event | Data |
|---|---|
| `start` | `{"conversation_id": "conv_8c1e", "message_id": "msg_01"}` |
| `step` | `{"id": "s1", "tool": "certified", "label": "Sales by month", "status": "running"}`, then the same `id` with `"status": "done"` or `"failed"`. `tool`: `certified`, `code`, `market`, `documents`, `web`. With `certified`: `metric` (`name`, `version`, `definition`). With `code`: `code` (the Python code that ran). |
| `text` | `{"delta": "You sold $649,958.80 in 2025. "}` |
| `chart` | `{"id": "c1", "provenance": "certified", "chart": {...}, "metric": {...}}`; for `market`: `benchmark`, `source` and `published` instead of `metric` |
| `table` | `{"id": "t1", "provenance": "exploratory", "title": "...", "columns": [...], "rows": [[...]]}`, same optional fields as `chart` |
| `citations` | `{"covered": true, "items": [{"id": "D6", "doc": "atlas_context.pdf", "section": "Store closures", "excerpt": "...", "score": null}]}` |
| `sources` | `{"items": [{"id": "W1", "title": "...", "url": "https://...", "published": "2026-10-12"}]}` |
| `blocked` | `{"message": "This request was blocked by the safety system."}` |
| `error` | `{"code": "internal", "message": "..."}` |
| `done` | `{}` |

Example `market` fields: `"benchmark": "Ontario retail trade, excluding motor vehicle and parts
dealers and gasoline stations"`, `"source": "Statistics Canada, table 20-10-0056-01"`,
`"published": "2026-08"` (latest month published).

Rules:

- `start` comes first; `done` or `error` comes last.
- Several `chart`, `table` and `step` events are allowed per answer; at most one `citations` and
  one `sources`.
- `covered: false` in `citations` means the user's document does not cover the question.
- `score` is `null` in `full` mode; in `rag` mode it is the calibrated reranker score.
- Text may contain references `[D<n>]` (a document section) and `[W<n>]` (a web source), matching
  `\[(D|W)(\d+)\]`. Each `D` reference matches an item of `citations`, each `W` reference an item
  of `sources`. These events may arrive after the text that references them.

## 8. Chart spec

The `chart` field of a `chart` event:

```json
{
  "type": "line",
  "title": "Monthly sales, Toronto - Queen Street",
  "x": {"label": "Month", "values": ["2025-01", "2025-02", "2025-03", "2025-04"]},
  "series": [
    {"name": "Sales", "values": [14972.81, 12613.95, 2003.68, 14435.76]}
  ],
  "unit": "CAD"
}
```

- `type`: `line`, `bar`, `bar_horizontal` (top N), `area`, `waterfall`.
- `waterfall`: a `measure` array gives each bar's role: `absolute` (start), `relative` (change),
  `total` (end).
- A series may set `"style": "dashed"`.
- `unit`: `CAD`, `%`, `count`, `days`.

## 9. `GET /api/overview?dataset_id=...` (later)

Tiles and charts computed directly by the certified functions, without the model:

```json
{
  "tiles": [
    {"id": "sales_ytd", "label": "Sales, Jan to Aug 2026", "value": 420781.22, "unit": "CAD", "delta": 0.0506,
     "provenance": "certified", "metric": {"name": "sales_total", "version": 1}}
  ],
  "charts": [{"id": "c1", "provenance": "certified", "chart": {}, "metric": {}}]
}
```

`delta`: year-over-year change, as a fraction (0.0506 = +5.06%).

## Changelog

| Version | Date | Change |
|---|---|---|
| 1 | 2026-10-31 | First version. |
