# 0002. Numbers come from tested functions or from code the user can read

- Status: Accepted
- Date: 2026-10-31

## Context

A language model asked "how much did we sell in 2025?" can produce a plausible number without
computing it. Even when it writes code, it chooses definitions on its own: keep or drop duplicate
rows, count "Walk-in" as a customer or not, include returns or not. Two runs of the same question
can give two different answers, both presented with the same confidence.

## Decision

The model never writes a number in an answer that a tool did not return. Numbers come from one of
two places, and the answer says which:

- **Certified**: a function with a fixed, versioned definition (a YAML card plus code), tested on
  small files computed by hand and on the Atlas sample. If a column it needs is missing, it
  refuses instead of guessing.
- **Exploratory**: code the agent writes for this question in Code Interpreter. The code is shown
  to the user.

The agent prefers a certified function whenever one fits the question.

## Consequences

- Every certified metric costs a definition, a function and tests. The list stays short on
  purpose (the common questions), and Code Interpreter covers the rest.
- Tool choice becomes something to measure: the evaluation suite counts how often a question that
  a certified function covers actually goes through it.
- The frontend shows the label on every chart and table, and a "How was this calculated" panel.

## Options considered

- Code Interpreter only: flexible, but definitions drift between runs.
- Certified functions only: reliable, but any question outside the list gets no answer.
