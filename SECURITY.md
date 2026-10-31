# Security

Please report a vulnerability privately through
[GitHub security advisories](https://github.com/Cedric0518/oyeva-sales/security/advisories/new),
not in a public issue.

What this project does to limit risk:

- No access keys: Azure services are called with managed identity
  ([decision 0005](docs/decisions/0005-no-keys.md)).
- Uploaded files are scanned with Prompt Shields before they reach the model
  ([decision 0006](docs/decisions/0006-prompt-shields-at-upload.md)), and the agent runs behind a
  Foundry guardrail.
- Uploaded files live in Blob Storage under the session and are deleted after seven days.
- Web searches never include data from the user's files.
