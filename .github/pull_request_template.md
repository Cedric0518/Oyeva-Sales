## What

<!-- One or two sentences. -->

## Why

<!-- The problem this solves, or the plan step it completes. -->

Closes #

## How it was tested

<!-- Commands run and what they showed. For the frontend: what to look at on screen. -->

- [ ] `ruff check .` and `pytest` pass (backend)
- [ ] `npm run build` and `npm run test` pass (frontend)

## Measurements

<!-- Required when this changes agent instructions, a model, embeddings, a reranker or a
threshold. Before and after, same cases, reports committed in evals/results/. Otherwise: n/a. -->

| Measure | Before | After |
|---|---|---|
| | | |

## Checklist

- [ ] No key, token or connection string in the diff
- [ ] `docs/contract.md` unchanged, or this pull request has the `contract` label and updates both sides
- [ ] A decision record in `docs/decisions/` if a choice could be questioned later
