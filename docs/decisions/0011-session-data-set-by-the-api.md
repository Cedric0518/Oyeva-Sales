# 0011. The API sets the session data; one Foundry conversation per chat

- Status: Accepted
- Date: 2026-11-05

## Context

Until B4 the agent had the Atlas file attached to its definition: Code Interpreter analyzed Atlas
whatever file the user uploaded, and a new agent version per upload would have been the only way
to change that (agent versions are immutable). The B4 loop chained the requests of one question
with `previous_response_id`, and did not keep the questions of a chat together.

Two Foundry features answer both points:

- **Structured inputs**: placeholders such as `{{sales_file_id}}` in the agent definition,
  replaced at each request by values sent in `extra_body["structured_inputs"]`. They work in the
  instructions and in the `file_ids` of an automatic Code Interpreter container.
- **Conversations**: `openai.conversations.create()`, then every request of the chat, including
  the one that sends function results back, passes `conversation=`. Foundry asks for function
  results within 10 minutes.

## Decision

- The API, never the model, sets the data of the session. The certified functions run on the
  session's data in the API. Code Interpreter gets the same rows, as read by the API, through the
  structured input `sales_file_id` (the file appears as `sales_data.csv`). The structured input
  `dataset` puts what the API read in the instructions: rows, dates, the columns of each role, the
  store names, the province.
- One chat is one Foundry conversation. Function results always go back to the conversation, even
  when the loop stops: the last request then sets `tool_choice: "none"`, so the agent answers in
  words and no call stays without its output. A conversation that ended with an error is not
  continued: the next message starts a new one.
- A request waits at most 90 seconds (`AGENT_REQUEST_SECONDS`) and a turn at most 180 seconds.

## Consequences

- One agent version serves every session; uploading a file creates no version.
- The same file content is uploaded to Foundry once per API instance. Nothing deletes these files
  yet: the cleanup goes with the Blob Storage lifecycle (B6).
- Names from the file reach the instructions. They are cleaned (one line, no braces, 60
  characters at most) and introduced as data, not instructions; Prompt Shields at upload (B8)
  checks them.
- Code Interpreter reads a clean CSV rather than the original: its numbers start from the same
  rows as the certified functions, but it does not see the other sheets of an Excel file.
- A conversation that ended with an error loses its history for the next message.

## Options considered

- A new agent version per upload: works, but fills the agent with one version per session.
- Attaching the file to a conversation item (`input_file`): files given this way are not mounted
  in the Code Interpreter container (Microsoft Q&A, 2026).
- Keep `previous_response_id`: works inside one question, but each question would start without
  the previous ones, and nothing in the portal groups a chat.
