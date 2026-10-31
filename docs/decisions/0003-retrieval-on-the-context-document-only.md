# 0003. Retrieval runs on the user's context document only

- Status: Accepted
- Date: 2026-10-31

## Context

Users upload two different things: a sales file (rows to compute on) and, optionally, a document
that explains their business (store closures, price changes, what a column means). Embedding the
rows of a sales file and retrieving them by similarity would be a way to get wrong totals.

## Decision

- The sales file is only ever read by code (certified functions, Code Interpreter).
- Retrieval (embeddings, hybrid search in Azure AI Search, reranking) runs on the context document
  only: Markdown as is, PDF and Word converted to Markdown by Azure Content Understanding.
- Below a size threshold, the whole document goes into the conversation instead of being
  searched. The threshold is measured on documents of increasing length, not guessed; it starts at
  8,000 tokens (`FULL_DOC_MAX_TOKENS`).
- Answers cite the section they rely on (`[D6]`). When the best reranked passage scores below a
  calibrated threshold, the answer says the document does not cover the question.

## Consequences

- Retrieval is evaluated on its own terms: expected section per question, and questions the
  document does not cover.
- The same terrain serves the retrieval benchmark (OpenAI and Cohere embeddings, Cohere Rerank 5,
  other rerankers), with the provider chosen by an environment variable.
- A short document never goes through search at all, which removes a failure mode for most users.

## Options considered

- Always retrieve: adds misses on short documents for no gain.
- Never retrieve (always the whole document): breaks on long handbooks and costs tokens on every
  question.
