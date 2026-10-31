#!/usr/bin/env bash
# One-time GitHub setup for Oyeva Sales: repository settings, labels, milestone, project board,
# the issues of the build plan, and the rules that protect main.
#
# Run from the repository root, after the first push:
#   gh auth refresh -s project      # once: lets gh create the project board
#   bash scripts/github_setup.sh
#
# Safe to re-run: labels are updated in place; the milestone, the project, existing issues
# (same title) and the ruleset are skipped.
set -euo pipefail

REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)
OWNER=${REPO%%/*}
MILESTONE="v2.0 - Demo"
PROJECT_TITLE="Oyeva Sales"
echo "Repository: $REPO"

gh project list --owner "$OWNER" --limit 1 > /dev/null 2>&1 || {
  echo "gh cannot manage projects yet. Run: gh auth refresh -s project"
  exit 1
}

# 1. Repository settings ---------------------------------------------------------------------
gh repo edit "$REPO" \
  --enable-issues --enable-projects --enable-wiki=false \
  --enable-rebase-merge --enable-squash-merge --enable-merge-commit=false \
  --delete-branch-on-merge > /dev/null
gh api -X PUT "repos/$REPO/private-vulnerability-reporting" > /dev/null 2>&1 \
  && echo "private vulnerability reporting: on" \
  || echo "private vulnerability reporting: turn it on in Settings > Security"
echo "settings: done"

# 2. Labels ----------------------------------------------------------------------------------
label() {
  gh label create "$1" --repo "$REPO" --color "$2" --description "$3" --force > /dev/null
  echo "label: $1"
}
label "area: backend"     "5319E7" "FastAPI, agent loop, certified metrics, checks"
label "area: frontend"    "1D76DB" "React app in frontend/"
label "area: azure"       "0E8A16" "Azure and Foundry resources, deployment"
label "area: rag"         "FBCA04" "Context documents, search, reranking"
label "area: evals"       "C2E0C6" "Evaluation suite and measurements"
label "area: security"    "B60205" "Guardrails, Prompt Shields, attacks"
label "type: step"        "BFD4F2" "A step of the build plan"
label "type: experiment"  "D4C5F9" "A measurement that decides something"
label "contract"          "E99695" "Changes docs/contract.md"
label "blocked"           "000000" "Waiting on something outside the repository"

# 3. Milestone -------------------------------------------------------------------------------
MILESTONES=$(gh api "repos/$REPO/milestones?state=all" -q '.[].title')
if grep -qxF "$MILESTONE" <<< "$MILESTONES"; then
  echo "milestone: exists"
else
  gh api "repos/$REPO/milestones" \
    -f title="$MILESTONE" \
    -f due_on="2026-11-06T23:59:59Z" \
    -f description="First complete version: upload, checks, certified and exploratory answers, market benchmark, context documents, web context, guardrails, traces, evaluation." \
    > /dev/null
  echo "milestone: created"
fi

# 4. Project board ---------------------------------------------------------------------------
PROJECT=$(gh project list --owner "$OWNER" --format json \
  -q ".projects[] | select(.title == \"$PROJECT_TITLE\") | .number" | head -n 1)
if [ -z "$PROJECT" ]; then
  PROJECT=$(gh project create --owner "$OWNER" --title "$PROJECT_TITLE" --format json -q .number)
  gh project link "$PROJECT" --owner "$OWNER" --repo "$REPO" > /dev/null
  echo "project: created (#$PROJECT)"
else
  echo "project: exists (#$PROJECT)"
fi

# 5. Issues ----------------------------------------------------------------------------------
EXISTING=$(gh issue list --repo "$REPO" --state all --limit 300 --json title -q '.[].title')

issue() {  # issue "<title>" "<labels>"  (body on stdin)
  local title=$1 labels=$2 body url
  body=$(cat)
  if grep -qxF "$title" <<< "$EXISTING"; then
    echo "issue exists: $title"
    return
  fi
  url=$(gh issue create --repo "$REPO" --title "$title" --label "$labels" \
    --milestone "$MILESTONE" --assignee "@me" --body "$body")
  gh project item-add "$PROJECT" --owner "$OWNER" --url "$url" > /dev/null
  echo "issue created: $url"
}

issue "B0: Prepare billing, budget, repository and early checks" "type: step,area: azure" <<'EOF'
Target: Sat Oct 31.

## Goal
Lift the limits of the trial subscription and start early whatever depends on others.

## Tasks
- [ ] Switch the subscription to pay-as-you-go; note what happens to the remaining credit
- [ ] Budget `budget-oyeva-sales` (100 CAD a month, alerts at 50, 80 and 100%)
- [ ] v1 repository: annotated tag `v1-local-mcp` on `ea85e786`, pushed; README points here
- [ ] This repository: scaffold on `main`, GitHub setup script run
- [ ] Atlas sample data in `evals/data/atlas/`, through a pull request
- [ ] Ask for early access to Jev (typesafe.ai)
- [ ] Foundry catalog: can Cohere Rerank 5 (Fast, Pro) and Cohere Embed v4 be deployed on this subscription, at what price?
- [ ] Is Content Understanding available in East US 2?

## Done when
- [ ] The tag shows on GitHub, this repository has its scaffold and the Atlas data
- [ ] The three checks (Jev, Cohere, Content Understanding) have a written answer in a comment here
EOF

issue "B1: Azure resources without keys" "type: step,area: azure" <<'EOF'
Target: Sat Oct 31.

## Goal
Everything else rests on these resources, and the environment holds no key from day one
(see `docs/decisions/0005-no-keys.md`).

## Tasks
- [ ] Resource group `rg-oyeva-sales` (East US 2)
- [ ] Storage account, anonymous blob access off; containers `uploads`, `outputs`, `reference`; lifecycle rule deleting `uploads/` and `outputs/` blobs after 7 days
- [ ] Foundry project `oyeva-sales`; check the existing deployments (`gpt-4.1-mini`, `gpt-5-mini`) are usable from it
- [ ] Deploy `text-embedding-3-small` (and Cohere models if B0 says it is possible)
- [ ] Azure AI Search `srch-oyeva-sales`, Basic tier, managed identity, semantic ranker
- [ ] Application Insights `appi-oyeva-sales`, connected to the Foundry project
- [ ] Key Vault `kv-oyeva-sales`, RBAC mode
- [ ] Roles for the developer account: Storage Blob Data Contributor, Search Service Contributor, Search Index Data Contributor, Foundry User, Cognitive Services User
- [ ] `scripts/check_access.py` with `DefaultAzureCredential`: list containers, list indexes, call the project

## Done when
- [ ] `python scripts/check_access.py` prints three OK
- [ ] `.env` holds no key

## What this teaches
RBAC, `DefaultAzureCredential`, Blob lifecycle rules. Roles take minutes to apply.
EOF

issue "B2: Foundry agent, in the portal then in code" "type: step,area: backend,area: azure" <<'EOF'
Target: Sat Oct 31.

## Goal
Understand the difference between a deployed model (v1) and an agent managed by Foundry, and find
how to retrieve the files Code Interpreter produces.

## Tasks
- [ ] Portal: agent `oyeva-sales-agent` (`gpt-4.1-mini`), short instructions, Code Interpreter, `atlas_sales.xlsx` attached
- [ ] Ask and compare with `answers.json`: sales 2025 (expected $649,958.80, duplicates included); Queen Street monthly 2025 (dip in March, $2,003.68); profit margin 2025 (the file has no costs: the agent must say so)
- [ ] Note whether the agent notices the duplicates and "Walk-in" on its own
- [ ] `scripts/try_agent.py`: `AIProjectClient`, agent version, conversation, Responses API (exact names checked in the SDK docs)
- [ ] Ask for a chart written to `chart_monthly.json` in the contract format; download it from the script

## Done when
- [ ] The script prints the executed code and saves a valid `chart_monthly.json`

## What this teaches
Agents, versions, conversations, Responses API output items, the Code Interpreter sandbox, and
why free code is not enough (the definitions the agent picks on its own).
EOF

issue "B3: Certified metrics, upload checks and retail benchmark" "type: step,area: backend" <<'EOF'
Target: Sun Nov 1.

## Goal
The core promise: numbers that always have the same definition, and are tested
(see `docs/decisions/0002-numbers-come-from-code.md` and `0004-provincial-retail-benchmark.md`).

## Tasks
- [ ] Column roles (`api/checks/roles.py`): date, amount, customer, product, quantity, unit price, store or region, order id, target (possibly in another sheet, `Targets.target` for Atlas)
- [ ] Checks (`api/checks/`): duplicates, months without sales per store, name variants, quantity x price vs amount (0.01 tolerance), dates out of range, placeholder customer, returns
- [ ] Metrics (`api/metrics/`): one YAML card (name, version, definition, required roles, refusals) and one function each; result or refusal
- [ ] Market (`api/market/`): Statistics Canada table 20-10-0056-01, dated copy in `reference/`, province benchmark excluding motor vehicle and parts dealers and gasoline stations (check whether the total exists per province; otherwise compute it), year-over-year growth on the same months, unadjusted series
- [ ] Tests: per function a 10 to 20 line file computed by hand, one refusal test; regression on Atlas against `answers.json`

## Done when
- [ ] `pytest` passes; every chart spec follows `docs/contract.md`
- [ ] Atlas values match `answers.json`; checks match the upload example of the contract
- [ ] One commit per metric

## What this teaches
Writing a definition that does not move, and what "certified" means in practice.
EOF

issue "B4: Function tools wired to the agent" "type: step,area: backend" <<'EOF'
Target: Sun Nov 1 to Mon Nov 2.

## Goal
The agent prefers a certified function to free code whenever a question fits one.

## Tasks
- [ ] One JSON schema per function; never a file path in the parameters (the API fixes the session's dataset)
- [ ] Versioned instructions in `api/agent_instructions.md`: when to use each tool, numbers only from tools, `[D3]` and `[W1]` references, the v1 honesty rule, warnings from the checks, the recommendation rule, no internal data in web searches
- [ ] Tool loop in `api/agent.py`: max 5 tool rounds, stop after two identical failures
- [ ] `scripts/try_tools.py`
- [ ] Mini measurement: 10 certified questions x 3 runs, count the right function

## Done when
- [ ] "How much did we sell in 2025?" goes through the sales metric 10 times out of 10 and answers $649,958.80 ($649,865.65 without duplicates)
- [ ] The measurement is committed with its result
EOF

issue "B5: FastAPI routes and SSE stream" "type: step,area: backend" <<'EOF'
Target: Mon Nov 2.

## Goal
The single door of the frontend, following `docs/contract.md` to the letter.

## Tasks
- [ ] Routes `/api/health`, `/api/upload`, `/api/sample`, `/api/chat` (overview later)
- [ ] `X-Session-Id` required (valid UUID), otherwise `missing_session`
- [ ] `/api/chat` as `text/event-stream`: map the agent stream to the contract events
- [ ] `/api/sample` loads Atlas (xlsx, notes in Markdown, `ON`)
- [ ] CORS from `ALLOWED_ORIGINS`; size limits (20 MB file; 5 MB and 50 pages document)
- [ ] `tests/test_contract.py`: pydantic models checked against the examples of the contract

## Done when
- [ ] `curl -N` on `/api/chat` shows events as they come
- [ ] The frontend in `live` mode against `localhost:8000` does an upload and a certified question end to end
EOF

issue "B6: Session files in Blob Storage" "type: step,area: backend,area: azure" <<'EOF'
Target: Mon Nov 2.

## Goal
Session files live in the Azure account, organized for automatic cleanup.

## Tasks
- [ ] `api/storage.py` with `DefaultAzureCredential`: original file, `data.parquet`, `meta.json`, `checks.json`, `context/`, charts in `outputs/`

## Done when
- [ ] After an upload, blobs appear at the right path in the portal
- [ ] Upload and questions read and write Blob Storage without a key
EOF

issue "B7: Deploy the API on Container Apps" "type: step,area: azure" <<'EOF'
Target: Mon Nov 2.

## Goal
From "works on my machine" to a public API with a managed identity.

## Tasks
- [ ] `Dockerfile` (`python:3.12-slim`, `uvicorn`) or `az containerapp up --source .`; app `ca-oyeva-api`
- [ ] Managed identity with the same roles as the developer account in B1
- [ ] Environment variables: endpoints only
- [ ] External ingress, at least 1 replica during demo week
- [ ] Check that SSE is not buffered by the ingress

## Done when
- [ ] `/api/health` answers on the public URL
- [ ] The local frontend, pointed at it, does an upload and a streamed question
EOF

issue "B8: Prompt Shields on uploads" "type: step,area: security" <<'EOF'
Target: Mon Nov 2 or Tue Nov 3.

## Goal
Close the side door: uploaded content reaches the model through our tools and Code Interpreter,
which the agent guardrail does not check (see `docs/decisions/0006-prompt-shields-at-upload.md`).

## Tasks
- [ ] `api/shields.py`: distinct values of text columns and each document section, in batches
- [ ] Flagged cell -> `[removed]` and reported in the checks; flagged section -> `removed_sections`
- [ ] Replay the v1 indirect attacks (hidden instruction in a description, then in a cell)
- [ ] Measure false positives on Atlas (file and notes)

## Done when
- [ ] Both v1 attacks are stopped at upload, with no false positive on Atlas, measured and committed
EOF

issue "B9: Context documents and retrieval" "type: step,area: rag" <<'EOF'
Target: Tue Nov 3.

## Goal
The "Your documents" label, and the ground for the retrieval benchmark
(see `docs/decisions/0003-retrieval-on-the-context-document-only.md`).

## Tasks
- [ ] `api/documents/convert.py`: PDF and Word to Markdown with Content Understanding (Layout analyzer); `.md` as is
- [ ] `sections.py`: split by headings, number D1, D2...; long sections re-split (about 800 tokens); no headings -> split by size
- [ ] Switch rule: below `FULL_DOC_MAX_TOKENS` whole document, above search (Atlas notes: whole)
- [ ] Index `idx-oyeva-docs`: `session_id` and `dataset_id` filterable, `title` and `content` searchable, `embedding_openai` (1536) and `embedding_cohere`, semantic configuration
- [ ] `embed.py` (`EMBED_BACKEND`), `rerank.py` (`RERANK_BACKEND`: none, semantic, cohere, jev)
- [ ] `search.py` (`search_documents`): hybrid search filtered on the session, 20 candidates, rerank, keep 3; `covered: false` below `NOT_COVERED_THRESHOLD`
- [ ] Delete a session's passages at cleanup
- [ ] Tests: splitting; the 13 questions of `doc_questions.json` with search forced on the Atlas notes

## Done when
- [ ] The same question on the notes in Markdown, PDF and Word returns the same section
- [ ] The 4 out-of-scope questions of `doc_questions.json` return `covered: false`
- [ ] The frontend shows `[D6]`, the documents panel and the not-covered notice
EOF

issue "B10: Web context, agent guardrail and attacks" "type: step,area: security" <<'EOF'
Target: Wed Nov 4.

## Goal
Add the Context source, and close what can be closed on the Foundry side.

## Tasks
- [ ] Grounding with Bing resource `bing-oyeva-sales`, connected to the project, tool added to the agent (queries leave the Azure compliance boundary: no internal data in them)
- [ ] Guardrail `guardrail-oyeva-sales` assigned to the agent: user prompt attacks blocked, indirect attacks on tool responses blocked (effective for Bing)
- [ ] Replay the v1 attacks: jailbreak in the question -> `blocked` event; hidden instruction in a document and in a cell -> stopped by B8
- [ ] On 10 questions that trigger the web, read the Bing queries in the traces: no customer name, no amount

## Done when
- [ ] The jailbreak shows `blocked` in the interface; the Bing queries are clean; results committed in `evals/results/`
EOF

issue "B11: End-to-end traces" "type: step,area: backend,area: azure" <<'EOF'
Target: Wed Nov 4.

## Goal
Follow one question end to end: which tool, how long, which error.

## Tasks
- [ ] OpenTelemetry in the API with `azure-monitor-opentelemetry`: one span per upload, per tool call, per search, `conversation_id` as attribute

## Done when
- [ ] In Application Insights, one question of each kind (certified, code, market, documents, web) is visible end to end with its steps and durations
EOF

issue "B12: Evaluation suite and measurements" "type: step,area: evals" <<'EOF'
Target: Thu Nov 5.

## Goal
What makes the demo credible to someone who comes from audit.

## Tasks
- [ ] `evals/` rewritten to call the deployed API over HTTP. Case types: numbers (oracle `answers.json`), tool choice, documents (expected section), not covered, market (benchmark and latest month present), warnings raised (July 2025 online, duplicates), attacks
- [ ] Atlas plus 1 or 2 other generated files with their documents, about 20 questions, several runs each; the report keeps the commit, the model, `EMBED_BACKEND`, `RERANK_BACKEND` and the threshold
- [ ] Optional: groundedness judged by `gpt-5-mini`, scored against human labels
- [ ] Read the answers, not only the score

## Done when
- [ ] Reports are committed; known failures are listed in a comment; the demo questions pass on every run
EOF

issue "B13: Demo rehearsal" "type: step,area: evals" <<'EOF'
Target: Thu Nov 5.

## Tasks
- [ ] A six-question scenario on Atlas showing the five labels, one "not covered" ("Why did Hamilton sales drop in 2026?") and one block
- [ ] A plan B if Bing or a Cohere model fails during the demo

## Done when
- [ ] The scenario runs twice in a row without a hitch
EOF

issue "F1: Frontend scaffold, upload and data report on the mock backend" "type: step,area: frontend" <<'EOF'
Target: Sat Oct 31 to Sun Nov 1. Written by Claude Code on `frontend/f1-upload`.

## Done when
- [ ] Vite project (React 19, TypeScript strict), design tokens from `docs/brand/`, `AppShell`
- [ ] `ApiClient` interface with `MockApiClient` (and an empty `LiveApiClient`)
- [ ] `UploadPanel` (file, optional document, province, "Use sample data", validation errors) and `DataReport` (checks, column roles, document card)
- [ ] The mock upload flow works on screen with the contract example
- [ ] `npm run build` and `npm run test` pass
EOF

issue "F2: Streaming chat, provenance labels and charts" "type: step,area: frontend" <<'EOF'
Target: Mon Nov 2. Written by Claude Code on `frontend/f2-chat`.

## Done when
- [ ] Streaming chat with a tested SSE parser (POST with `fetch`)
- [ ] `ProvenanceBadge` (five labels, never color alone), `ChartView` (line, bar, bar_horizontal, area, waterfall), `DataTable`, `HowCalculatedDrawer`
- [ ] Mock scenarios Certified, Exploratory and Market on screen
EOF

issue "F3: Document references, citations and live API" "type: step,area: frontend" <<'EOF'
Target: Tue Nov 3. Written by Claude Code on `frontend/f3-citations`.

## Done when
- [ ] `[D]` and `[W]` reference parser tested, including references split across two `text` events
- [ ] Reference-to-citation matching, `DocumentsPanel`, `NotCoveredNotice`, document card
- [ ] `LiveApiClient` connected to the local API (B5)
EOF

issue "F4: Web sources, blocked and error states, deployment" "type: step,area: frontend,area: azure" <<'EOF'
Target: Wed Nov 4. Written by Claude Code on `frontend/f4-web-and-states`; deployment with the owner.

## Done when
- [ ] `WebSourcesBox`, `BlockedNotice`, error states and network banner
- [ ] Deployed on Azure Static Web Apps (`swa-oyeva-sales`), API URL set at build time, CORS allowed on the API
EOF

issue "F5: Polish, accessibility pass and demo flow" "type: step,area: frontend" <<'EOF'
Target: Thu Nov 5. Written by Claude Code on `frontend/f5-polish`.

## Done when
- [ ] Keyboard access to chips, buttons, drawer (Escape closes, focus kept); AA contrast
- [ ] Correct at 1280 and 1440 px wide
- [ ] The demo flow runs without a hitch against the deployed API
- [ ] Overview tab if time allows
EOF

issue "Experiment: whole document or search, where is the threshold?" "type: experiment,area: rag,area: evals" <<'EOF'
## Question
Below which document size is it better to put the whole document in the conversation than to
search it? This sets `FULL_DOC_MAX_TOKENS` (8,000 for now, a guess).

## Setup
A long fictional handbook (20 to 30 pages, Markdown, PDF and Word, about 100 questions with the
expected section, about 20 out of scope), cut at 2, 5, 10, 20 and 30 pages. For each size: whole
document vs search (same embeddings, same reranker). Several runs per question.

## Reading rule, fixed before the results
For each size, the better mode is the one that cites the expected section more often, provided it
does not answer more out-of-scope questions. The threshold is the largest size where whole
document is not worse. Cost and latency break ties.

## Expected cost
To estimate before running (tokens per question x questions x sizes x runs).
EOF

issue "Experiment: retrieval benchmark, embeddings and rerankers" "type: experiment,area: rag,area: evals" <<'EOF'
## Question
Which embeddings and reranker should Oyeva Sales use on context documents: OpenAI
`text-embedding-3-small` or Cohere Embed v4; no reranker, Azure semantic ranker, Cohere Rerank 5
(Fast, Pro) or Jev?

## Setup
Same handbook and questions as the threshold experiment, search mode forced. Hybrid search, 20
candidates, 3 kept. Measures: expected section in the top 3, out-of-scope questions correctly
marked not covered (after calibrating the threshold per reranker on a separate set), latency, cost
per 1,000 questions. Vendor numbers are not used.

## Reading rule, fixed before the results
A setup replaces the default (OpenAI embeddings, no reranker) if it finds the expected section in
the top 3 more often on at least two of the three document sizes tested, without lowering the
not-covered accuracy, at an acceptable cost and latency for an interactive answer.

## Expected cost
To estimate before running.
EOF

# 6. Rules for main ---------------------------------------------------------------------------
RULESETS=$(gh api "repos/$REPO/rulesets" -q '.[].name')
if grep -qxF "main" <<< "$RULESETS"; then
  echo "ruleset: exists"
else
  gh api -X POST "repos/$REPO/rulesets" --input - > /dev/null <<'JSON'
{
  "name": "main",
  "target": "branch",
  "enforcement": "active",
  "conditions": {"ref_name": {"include": ["~DEFAULT_BRANCH"], "exclude": []}},
  "bypass_actors": [],
  "rules": [
    {"type": "deletion"},
    {"type": "non_fast_forward"},
    {"type": "required_linear_history"},
    {"type": "pull_request", "parameters": {
      "required_approving_review_count": 0,
      "dismiss_stale_reviews_on_push": false,
      "require_code_owner_review": false,
      "require_last_push_approval": false,
      "required_review_thread_resolution": true
    }},
    {"type": "required_status_checks", "parameters": {
      "strict_required_status_checks_policy": false,
      "required_status_checks": [{"context": "ci-ok"}]
    }}
  ]
}
JSON
  echo "ruleset: created (main now accepts pull requests only)"
fi

echo
echo "Done. Next: open the project board on GitHub and switch its view to Board."
