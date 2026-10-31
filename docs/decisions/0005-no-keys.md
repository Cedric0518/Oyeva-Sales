# 0005. No keys: managed identity everywhere

- Status: Accepted
- Date: 2026-10-31

## Context

The API talks to Foundry, Blob Storage, Azure AI Search, Content Safety and Content Understanding.
Each of them can be called with an access key. A key in a `.env` file ends up copied, pasted into
a chat or committed by mistake.

## Decision

- Every call uses Microsoft Entra ID through `DefaultAzureCredential`: `az login` on a developer
  machine, the managed identity of the Container App in production.
- Access is granted with Azure roles (RBAC), the narrowest that work.
- `.env` holds endpoints and settings only. `.env.example` is committed; `.env` is not.
- Later, GitHub Actions deploys with OpenID Connect (federated credentials), so the repository
  holds no Azure secret either.

## Consequences

- Role assignments take a few minutes to apply: a 403 right after granting a role is not
  necessarily a mistake.
- Some services or features may only accept keys; any exception gets its own record here.

## Options considered

- Keys in Key Vault: better than a `.env` file, but still a secret to rotate and to leak.
