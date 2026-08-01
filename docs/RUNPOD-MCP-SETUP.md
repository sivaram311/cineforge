# RunPod MCP setup (cineforge)

Lets an MCP-compatible agent (Cursor, Claude Code, etc.) manage RunPod infrastructure and search RunPod docs interactively for this project. Complements the direct-REST path in `src/cineforge/runpod_client.py` — it does not replace it.

> **Correction note:** An earlier version of this doc described a hosted-OAuth API MCP server at `https://mcp.getrunpod.io/` with a browser “Sign in with RunPod” flow. That was based on incorrect research and does **not** match RunPod’s current documentation. This file reflects the real setup from [RunPod’s MCP servers docs](https://docs.runpod.io/get-started/mcp-servers).

## Two MCP servers

RunPod publishes **two** separate MCP servers:

| Server | Package / URL | Auth | Role |
|--------|---------------|------|------|
| **API MCP** | `npx -y @runpod/mcp-server@latest` (stdio) | Requires a real `RUNPOD_API_KEY` in the client config `env` | Manage Pods, Serverless endpoints, templates, network volumes, container registries |
| **Docs MCP** | `https://docs.runpod.io/mcp` (HTTP) | None | Read-only docs search: feature explanations, code examples, configuration guides, general RunPod knowledge |

There is **no** hosted-OAuth browser sign-in for the API MCP in the current official client setup. Every supported client (Cursor, Claude Code, Claude Desktop, VS Code, Windsurf, Cline, Gemini CLI, Codex) launches the API server locally via `npx` and passes `RUNPOD_API_KEY`.

## What this repo ships (`.cursor/mcp.json`)

Project config includes both servers. The API key is **not** hardcoded:

```json
{
  "mcpServers": {
    "runpod": {
      "command": "npx",
      "args": ["-y", "@runpod/mcp-server@latest"],
      "env": {
        "RUNPOD_API_KEY": "${env:RUNPOD_API_KEY}"
      },
      "envFile": "${workspaceFolder}/.env"
    },
    "runpod-docs": {
      "url": "https://docs.runpod.io/mcp"
    }
  }
}
```

Cursor supports config interpolation (`${env:NAME}`) and, for STDIO servers, `envFile` ([Cursor MCP docs](https://cursor.com/docs/mcp)). That keeps this file safe to commit: no literal secret.

### Operator requirements (API MCP)

1. **Node.js 18+** on PATH (needed for `npx`).
2. A real RunPod API key available to Cursor when it starts the server, via either:
   - System / shell environment variable `RUNPOD_API_KEY` (what `${env:RUNPOD_API_KEY}` resolves), and/or
   - This project’s gitignored `.env` (loaded by `envFile: "${workspaceFolder}/.env"`).
3. Trust the locally launched `@runpod/mcp-server` process (it receives your key and calls the RunPod REST API on your behalf).

Desktop Cursor may not inherit vars from `.bashrc` / `.zshrc`. Prefer a system-level env var, launch Cursor from a shell that already exports the key, or rely on the project `.env` + `envFile`.

**Never commit a real key.** Official RunPod examples often show a literal `"your_api_key_here"` string in config; that is fine as a personal/global override (`~/.cursor/mcp.json`) but must not land in the shared repo file.

## Capabilities

### API MCP (`runpod`)

- Pod management (list / get / create / start / stop / update / delete)
- Serverless endpoint creation and configuration
- Template operations
- Network volume administration
- Container registry management

(Exact tool names follow `@runpod/mcp-server`; they wrap the [RunPod REST API](https://docs.runpod.io/api-reference/overview).)

### Docs MCP (`runpod-docs`)

- Feature explanations
- Code examples
- Configuration guides
- General RunPod knowledge queries

No spend/billing tools via MCP. Docs MCP needs no env vars; API MCP requires `RUNPOD_API_KEY`.

## Known gotchas

- DELETE endpoint calls can return `204 No Content`; some MCP clients mis-parse that as a JSON error. Harmless — the delete still succeeds.
- Newly created pods may return null `publicIp` / `portMappings` until initialized. Poll until ready; do not assume readiness on create.
- `${env:RUNPOD_API_KEY}` only resolves variables present in the Cursor process environment. If the key exists only in `.env`, `envFile` is what makes the local API MCP work.

## MCP vs REST (`runpod_client.py`)

| Path | Role |
|------|------|
| **MCP** (this doc) | Interactive / agent-driven exploration and one-off ops |
| **REST** (`src/cineforge/runpod_client.py`) | Reliable, scriptable, repeatable calls from the CLI / library — CI-safe automation |

They are complementary. Use MCP when an agent is driving the session; use the REST client when you need deterministic, repeatable automation.
