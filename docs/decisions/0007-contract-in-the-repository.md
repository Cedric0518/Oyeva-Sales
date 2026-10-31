# 0007. The API contract lives in the repository

- Status: Accepted
- Date: 2026-10-31

## Context

The frontend and the backend are written by different hands (the frontend by an AI coding agent,
the backend by the project owner) and progress in parallel. The frontend starts on a mock backend
before the real API exists. If the two sides drift, nothing breaks until the integration day.

## Decision

- `docs/contract.md` is the single source of truth for routes, payloads and streamed events.
- It changes only through a pull request labeled `contract`. That pull request either updates
  both sides or opens the issue that will update the other side.
- The backend checks its responses against the examples of the contract in tests (pydantic models).
  The frontend's mock backend returns the same examples.

## Consequences

- A change of mind costs a pull request, which is the point.
- The contract carries a version number and a changelog.

## Options considered

- Contract in a design document outside the repository: invisible to the coding agent and to
  reviewers, and out of date the first time someone forgets it.
- An OpenAPI file generated from FastAPI: good later, but the frontend needs the contract before
  the backend exists, and OpenAPI does not describe the streamed events well.
