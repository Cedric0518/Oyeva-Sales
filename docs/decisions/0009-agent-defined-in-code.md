# 0009. The agent is defined in code, with Code Interpreter attached directly

- Status: Accepted
- Date: 2026-11-03

## Context

The first version of `oyeva-sales-agent` was built in the new Foundry portal. The portal put Code
Interpreter in a toolbox, served to the agent over MCP. Each Code Interpreter call then ran in a new
container: the agent read the sales file again at every call and lost its Python state
(`NameError: name 'pd' is not defined`), with up to 8 calls for one question. The API will also need
what the portal cannot do: give each session its own file, and describe the certified functions
next to their code.

## Decision

- `scripts/create_agent.py` creates each agent version with `project.agents.create_version`, a
  `PromptAgentDefinition`, and `CodeInterpreterTool` attached directly (automatic container, file ids).
- The instructions live in `api/agent_instructions.md`, so each agent version can be traced to a commit.
- The portal is for exploring, reading traces and managing guardrails, not for defining the agent.

## Consequences

- Measured on the same question (Queen Street monthly sales, 2 runs each): the portal version made
  4 and 5 tool calls, each in its own container; the code version made 3 calls in one container per
  conversation, in 13.3 s and 16.8 s, with the same numbers. The duration of the portal version was
  not measured.
- With Code Interpreter attached directly, the code outputs were not in the response. The API will
  have to request them for the "How was this calculated" drawer (to check in B4).
- Files produced by Code Interpreter are linked in the answer (container file citations) and
  downloaded through the containers API. A file name chosen by the model is never used as a path.
- Giving each session its own file without a new agent version per session is still open (B4, B5).

## Options considered

- Keep the portal agent: quick to change by hand, but not reproducible from the repository, and its
  toolbox cost one container per call.
- A toolbox defined in code: possible, but we saw no benefit from a toolbox for a single agent.