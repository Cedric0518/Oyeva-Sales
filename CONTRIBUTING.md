# How work happens in this repository

## Who does what

- **Backend, Azure and Foundry**: written by the project owner.
- **Frontend**: written by an AI coding agent (Claude Code), in `frontend/` only, through pull
  requests that the owner reviews and merges. Its rules are in [CLAUDE.md](CLAUDE.md) and
  [frontend/CLAUDE.md](frontend/CLAUDE.md).
- **Design reviews and guidance**: an AI assistant (Claude) that explains, proposes and reviews,
  but does not commit.

## The cycle

1. **An issue first.** Every piece of work starts as an issue: a plan step (`B3`, `F2`...), an
   experiment, or a bug. It says what "done" means before any code is written.
2. **A branch per issue**, named after it:

   | Kind | Branch |
   |---|---|
   | Backend feature | `feat/b3-certified-metrics` |
   | Frontend milestone | `frontend/f1-upload` |
   | Bug fix | `fix/sse-buffering` |
   | Experiment | `exp/rerank-benchmark` |
   | Documentation | `docs/contract-v2` |
   | Tooling, data | `chore/atlas-sample-data` |

3. **Small commits**, in English, following [Conventional Commits](https://www.conventionalcommits.org/):
   `feat(metrics): add sales_total v1`, `fix(api): keep SSE unbuffered behind ingress`,
   `test(checks): duplicate rows on a hand-computed file`. Code taken from v1 is rewritten in its
   own commit that cites the v1 commit.
4. **A pull request** using the template: what, why, how it was tested, measurements if relevant,
   and `Closes #<issue>`.
5. **Checks must pass** (lint, tests, frontend build, scope check for frontend branches).
6. **Merge** with "Rebase and merge" to keep the small commits and a linear history ("Squash and
   merge" for a pull request whose commits are not worth keeping). The branch is deleted after.

`main` is protected: no direct push, no force push, pull requests only, checks required.

## Measurements before opinions

Any change to the agent instructions, a model, the embeddings, the reranker or a threshold:

- the reading rule is written in the issue **before** the results are seen;
- the evaluation runs before and after, on the same cases;
- both reports are committed in `evals/results/` with the commit, the model and the settings;
- the pull request quotes the numbers, and someone reads the answers, not only the score.

## The API contract

[docs/contract.md](docs/contract.md) is the source of truth between frontend and backend. A pull
request that changes it carries the `contract` label and updates both sides, or opens the issue
that will. See [decision 0007](docs/decisions/0007-contract-in-the-repository.md).

## Decisions

A choice that someone could reasonably question later gets a record in
[docs/decisions](docs/decisions), in the same pull request as the code it explains.

## Secrets

- No keys in the repository, in issues or in pull requests. Azure access goes through managed
  identity and `DefaultAzureCredential` ([decision 0005](docs/decisions/0005-no-keys.md)).
- `.env` is ignored; `.env.example` lists the variables with placeholder values.
- Sample data is fictional. No real customer data is ever committed.

## Local setup

Backend (Python 3.12):

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env        # then fill in the endpoints
az login
ruff check . && ruff format --check . && pytest
```

Frontend (Node 22):

```bash
cd frontend
npm ci
npm run dev                 # mock backend by default
npm run build && npm run test
```
