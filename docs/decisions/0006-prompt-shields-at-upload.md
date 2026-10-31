# 0006. Scan uploads with Prompt Shields

- Status: Accepted
- Date: 2026-10-31

## Context

Uploaded content reaches the model through our own tools: customer names returned by a certified
function, rows read by Code Interpreter, sections of the context document. Text hidden in a cell
or a document ("ignore your instructions and...") is an indirect prompt attack. In v1, the attack
tests showed that this side door was the one that mattered.

Foundry agent guardrails check tool responses only for some tools (Azure AI Search, Azure
Functions, OpenAPI, SharePoint, Fabric Data Agent, Bing Grounding, Bing Custom Search, Browser
Automation). Code Interpreter, MCP tools and function tools are not covered.

## Decision

- At upload, send the distinct values of the text columns and each section of the context document
  to Prompt Shields (document mode).
- A flagged cell is replaced by `[removed]` and reported in the checks. A flagged section is set
  aside and listed in `removed_sections`.
- The agent guardrail still blocks attacks in the user's question and in the responses of the
  tools it covers (Bing).

## Consequences

- One more call per upload, in batches.
- False positives are possible: they are measured on the Atlas sample (target: none) and on the
  v1 attack files (target: all caught).
- Two layers of defense instead of one, each tested on its own.

## Options considered

- Rely on the agent guardrail alone: it does not see the outputs of our function tools or of Code
  Interpreter.
