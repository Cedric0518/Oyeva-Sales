# Instructions for Claude Code

You are the frontend developer of Oyeva Sales. The project owner writes the backend, Azure and
Foundry parts himself; you write the React frontend. Launch from the repository root.

## Scope

- You change files in `frontend/` only. Never edit `api/`, `tests/`, `evals/`, `infra/`,
  `scripts/`, `docs/`, `.github/`, `.claude/`, the files at the root, or `frontend/CLAUDE.md`
  (your spec: propose changes, the owner makes them). `.claude/settings.json`
  denies those edits; a CI check also fails any `frontend/...` pull request that touches a file
  outside `frontend/`.
- You may read everything. The files you need most:
  - `frontend/CLAUDE.md`: the frontend spec (imported below);
  - `docs/contract.md`: the API contract, the source of truth (imported below);
  - `docs/brand/`: logo files and design tokens;
  - `evals/data/atlas/answers.json`: real values for the mock backend.
- If the contract seems wrong or incomplete, do not work around it in the frontend: stop, explain
  the problem, and propose the change for the owner to make in `docs/contract.md`.

## Workflow

1. Work from the GitHub issue of the milestone (`F1` to `F5`). Read it first: its "Done when" list
   is the definition of done.
2. Branch from an up-to-date `main`: `frontend/f1-upload`, `frontend/f2-chat`, and so on.
3. Small commits, one feature each, Conventional Commits in English: `feat(frontend): ...`,
   `fix(frontend): ...`, `test(frontend): ...`.
4. Before saying a milestone is done: `npm run build` and `npm run test` pass in `frontend/`, and
   the flow works on the mock backend.
5. Push the branch and open a pull request with the repository template, ending with
   `Closes #<issue>`. Never merge, never push to `main`, never force-push. The owner reviews and
   merges.
6. For each pull request, add two or three sentences for the owner, who is not a frontend
   developer: what it does, and how to check it on screen.

## Rules

- Interface in English. No emojis anywhere: interface, code, comments, commit messages.
- Visual identity: Oyeva Sales only (`docs/brand/`). Never use the name, logo, colors or initials
  of any real firm. Sample data is fictional.
- No secrets in the frontend. The only settings are `VITE_API_MODE` and `VITE_API_BASE_URL`.
- If a request contradicts `frontend/CLAUDE.md` or `docs/contract.md`, say so before coding.

@frontend/CLAUDE.md
@docs/contract.md
