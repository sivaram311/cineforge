# RunPod MCP setup (cineforge)

Lets an MCP-compatible agent (Cursor, Claude Code, etc.) manage RunPod Pods, Serverless endpoints, and jobs interactively for this project. Complements the direct-REST path in `src/cineforge/runpod_client.py` — it does not replace it.

## Path A — Hosted OAuth (wired in this repo)

`.cursor/mcp.json` uses RunPod's hosted MCP endpoint:

```json
{
  "mcpServers": {
    "runpod": {
      "url": "https://mcp.getrunpod.io/"
    }
  }
}
```

No API key is stored locally; this config is safe to commit.

### Manual step (required once per operator)

1. Open this repo in an MCP-compatible client (e.g. Cursor).
2. When the client connects to the `runpod` server, complete the **Sign in with RunPod** browser OAuth flow and approve access.

This cannot be done headlessly or non-interactively. Restrictive proxies that block outbound HTTP/SSE may also prevent the connection.

## Path B — Self-hosted npm (alternative for headless / CI)

For environments without an interactive browser (CI, remote agents), run the official npm package locally with a real API key:

```json
{
  "mcpServers": {
    "runpod": {
      "command": "npx",
      "args": ["-y", "@runpod/mcp-server@latest"],
      "env": {
        "RUNPOD_API_KEY": "your_actual_runpod_api_key_here"
      }
    }
  }
}
```

Requires Node 18+.

**Warning:** Never commit a real `RUNPOD_API_KEY`. If you put a real key in a config (or override) file, that file must be gitignored. Prefer env injection from a secrets store over committing credentials.

## Exposed MCP tools

**Pods:** `list-pods`, `get-pod`, `create-pod`, `start-pod`, `stop-pod`, `update-pod`, `delete-pod`

**Serverless:** `list-endpoints`, `get-endpoint`, `create-endpoint`, `update-endpoint`, `delete-endpoint`, `run-endpoint` (async; returns `jobId`), `runsync-endpoint`, `get-job-status`, `stream-job`

**GPU catalog (GraphQL-backed):** `list-gpu-types`, `list-data-centers`

There are no spend/billing tools via MCP. Path A needs no env vars; Path B requires `RUNPOD_API_KEY`.

## Known gotchas

- DELETE endpoint calls can return `204 No Content`; some MCP clients mis-parse that as a JSON error. Harmless — the delete still succeeds.
- Newly created pods return null `publicIp` / `portMappings` until initialized. Poll `get-pod`; do not assume readiness on create.
- Serverless tools (`run-endpoint`, `get-job-status`) target `api.runpod.ai/v2`; pod-management tools use the standard REST API. Mixing `templateId` vs `imageName` / `gpuPoolIds` on endpoint creation can cause schema mismatches.

## MCP vs REST (`runpod_client.py`)

| Path | Role |
|------|------|
| **MCP** (this doc) | Interactive / agent-driven exploration and one-off ops — manage pods, check endpoint status, browse GPU pricing conversationally |
| **REST** (`src/cineforge/runpod_client.py`) | Reliable, scriptable, repeatable calls from the CLI / library — CI-safe automation |

They are complementary. Use MCP when an agent is driving the session; use the REST client when you need deterministic, repeatable automation.
