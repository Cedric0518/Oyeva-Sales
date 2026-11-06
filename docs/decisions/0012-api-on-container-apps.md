# 0012. The API runs on Azure Container Apps, with one managed identity and no key

- Status: Accepted
- Date: 2026-11-06

## Context

The API ran on the developer's computer. The frontend on Static Web Apps, and anyone who tests
the product, need a public HTTPS address. The API streams answers (Server-Sent Events) for up to
180 seconds, reaches Foundry without a key (decision 0005), and will later need a scheduled job
(the Statistics Canada copy, B6). Until B6 it keeps the session files in memory.

## Decision

- **Azure Container Apps**, consumption plan, in `rg-oyeva-sales` (East US, decision 0008):
  environment `cae-oyeva-sales`, app `ca-oyeva-api`, external ingress on port 8000.
- **The image is built in Azure** by `az acr build` from the `Dockerfile`, into an Azure
  Container Registry (Basic) whose admin user stays disabled. The image holds the API code, the
  Atlas sample file and the committed Statistics Canada copy; `.dockerignore` keeps `.env`, local
  environments and outputs out.
- **One user-assigned managed identity, `id-oyeva-api`**, used to pull the image (AcrPull on the
  registry) and to call Foundry (the same Foundry role as the developer). It exists before the
  app, so its roles are in place when the first revision starts. `AZURE_CLIENT_ID` tells
  `DefaultAzureCredential` which identity to use.
- **Settings are addresses only**: project endpoint, agent name, allowed origins.
- **Exactly one replica** (minimum 1, maximum 1) until B6: the sessions live in the memory of the
  replica, and a second replica would not know them; one replica always on also avoids a cold
  start during the demo week. 1 vCPU and 2 GiB: Atlas is read in about 7 seconds and kept in
  memory.

## Consequences

- An always-on replica costs money even when nobody uses it: watch the budget, and set the
  minimum to 0 after the demo week.
- The ingress closes a connection that stays silent for about 240 seconds; a Foundry request
  waits at most 90 seconds (decision 0011), so a stream never stays silent that long.
- Each deployment is a new revision: a bad one can be rolled back to the previous one.
- Logs go to the Log Analytics workspace of the environment.

## Options considered

- `az containerapp up --source .`: one command, but it chooses the registry, its credentials and
  the identity by itself; the point of B7 is to set each of them explicitly.
- A system-assigned identity: it only exists once the app does; a user-assigned one receives its
  roles before the first revision, which keeps each step simple and visible.
- App Service: would work; Container Apps also brings scheduled jobs and scale to zero.
- Azure Functions: made for short calls, a poor fit for answers streamed over several seconds.
