# 0008. Dedicated Azure resources for v2, in East US

- Status: Accepted
- Date: 2026-11-02

## Context

The v1 Foundry resource `mini-data-science-assistant` (resource group `rg-data-assistant`, East US)
already had model deployments, and a second project could have been added to it. But the first
project of a resource is its default project, and other projects lack some features (OpenAI Batch,
fine-tuning, stored completions). Sharing the resource would also mix v1 and v2 deployments,
guardrails, role assignments and costs. Finally, `gpt-4.1-mini`, used in v1, is deprecated and
retires on 2027-04-14.

## Decision

- Everything for v2 lives in the resource group `rg-oyeva-sales`, in East US, the region of the v1
  resource. Content Understanding is available there.
- A new Foundry resource `aif-oyeva-sales`, whose default project is `oyeva-sales`. Its Application
  Insights (`aif-oyeva-sales-appinsights`) was created and connected with the project.
- Deployments, all Global Standard: `gpt-5.4-mini` (agent candidate), `gpt-5-mini` (judge, and second
  agent candidate), `text-embedding-3-small`, `Cohere-rerank-v5-fast`, `Cohere-Embed-V5-Fast`. The two
  chat models only change version when theirs expires (`OnceCurrentVersionExpired`), so that no
  measurement silently compares two model versions. The B4 measurement confirms the agent model.
- Storage `stoyevasales01`: shared key access off, anonymous access off, Microsoft Entra
  authorization by default in the portal, blob soft delete off, container soft delete on. A
  lifecycle rule deletes blobs under `uploads/` and `outputs/` modified more than 7 days ago;
  `reference/` is never touched.
- Azure AI Search `srch-oyeva-sales`, Basic tier: role-based access only, system-assigned identity,
  semantic ranker on the free plan.
- Developer roles: Storage Blob Data Contributor on the storage account, Search Service Contributor
  and Search Index Data Contributor on the search service, Foundry User on the resource group. Its
  data actions (`Microsoft.CognitiveServices/*`) also cover Content Safety and Content Understanding,
  so Cognitive Services User is not needed.
- `scripts/check_access.py` checks that each service answers to the signed-in identity.

## Consequences

- v1 stays untouched; deleting `rg-oyeva-sales` removes all of v2.
- Models had to be deployed again, and the regional quota is shared with v1.
- With blob soft delete off, a file deleted by a bug in our code cannot be recovered. A copy in
  `reference/` can be downloaded again, but a revised Statistics Canada series may differ, so each
  copy keeps its publication date.
- The lifecycle rule runs about once a day: files are deleted after about 7 days, not exactly 7.
- Azure AI Search Basic is billed by the hour, even when idle.

## Options considered

- A second project on the v1 resource: no new deployments, but a non-default project and shared
  costs and access.
- `gpt-4.1-mini` as the agent: measured in v1, but deprecated.
- Blob soft delete on: protects against our own bugs, but keeps users' deleted files 7 more days.
- Azure AI Search Free tier: no managed identity for Microsoft Entra ID and no semantic ranker, so it
  would need a key.