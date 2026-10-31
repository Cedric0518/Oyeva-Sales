# 0001. Start a new repository for v2

- Status: Accepted
- Date: 2026-10-31

## Context

Version 1, [mini-data-science-assistant](https://github.com/Cedric0518/mini-data-science-assistant),
is a local agent: Gradio, Ollama, an MCP server, LangGraph. Its evaluation reports cite commits and
can be replayed from them. Version 2 is a production agent on Microsoft Foundry with a different
stack (FastAPI, React, Azure services) and almost none of the running code of v1.

## Decision

Build v2 in this new repository. v1 stays as it is, frozen at the tag `v1-local-mcp`, with a link
to this project in its README.

## Consequences

- v1 stays reproducible: its reports still point to code that exists.
- What v2 takes from v1 (content hashing of datasets, splitting a document by headings, the
  honesty rule of the system prompt, the swappable model backend, the evaluation method) is
  rewritten on purpose, one commit per idea, each citing the v1 commit it comes from.
- Two repositories to explain instead of one; the v1 README and this README link to each other.

## Options considered

- Build on top of v1: every path in its reports would break, and the history would mix two
  different products.
- A `v2/` folder inside v1: same problem, and dependencies that conflict.
