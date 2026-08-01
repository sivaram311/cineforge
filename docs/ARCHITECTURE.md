# cineforge architecture (Inception skeleton)

## Purpose

cineforge orchestrates RunPod GPU cloud compute to turn text/image prompts into video clips that will eventually assemble into a longer piece. This document describes the **Day-1 skeleton**: a Python CLI + library that talks to RunPod over its **REST API**. Interactive agent-driven control via RunPod's MCP server is a related but separate path (see below).

## Module layout

```
src/cineforge/
  __init__.py          # package version
  cli.py               # argparse entrypoint (`cineforge` console script)
  runpod_client.py     # RunPod Serverless REST wrapper
tests/
  test_runpod_client.py
docs/
  ARCHITECTURE.md      # this file
```

Reserved machine ports (not bound yet): DEV `:3400` (api), `:3401` (future UI), `:3402` (future worker).

## Call path (direct REST)

```
cineforge generate --prompt "..."
        │
        ▼
   cli.py  ──parse args──►  runpod_client.generate()
                                │
                                ├─ POST /v2/{endpoint_id}/run
                                │     Authorization: Bearer $RUNPOD_API_KEY
                                │     body: {"input": {"prompt": "...", ...}}
                                │
                                ├─ GET  /v2/{endpoint_id}/status/{job_id}
                                │     (poll until COMPLETED / FAILED / …)
                                │
                                └─ return status payload (incl. output URLs / data)
```

Config is loaded from the environment via `python-dotenv` (`.env` locally; never committed). Required vars: `RUNPOD_API_KEY`, `RUNPOD_ENDPOINT_ID`.

The skeleton submits a prompt-shaped `input` payload. Later Construction Bolts will extend params (duration, resolution, I2V image refs, ComfyUI workflow JSON) and wire toward WAN 2.6 / `worker-comfyui` endpoints.

## RunPod MCP vs this code path

| Path | Role | Status |
|------|------|--------|
| **REST client** (`runpod_client.py`) | Deterministic pipeline orchestration: submit → poll → fetch from application/CLI code | Scaffolded here |
| **RunPod MCP server** (`@runpod/mcp-server` or hosted `https://mcp.getrunpod.io/`) | Interactive / agent-driven: create Pods, deploy Serverless endpoints, browse GPUs/pricing, submit/monitor jobs from an MCP client (Cursor, Claude, etc.) | **Not built into cineforge yet** — a future option for operator workflows and infra setup, complementary to (not a replacement for) the in-process REST client |

Use MCP when an assistant needs to manage RunPod infrastructure conversationally. Use this library when cineforge itself must run generation jobs as part of an automated DLC pipeline.

## Out of scope (Inception)

- No web UI (`:3401`), no worker process (`:3402`), no PREPROD/PROD deploy (F:/G:).
- No live RunPod calls required for unit tests (HTTP is mocked).
- Auth beyond a single-operator local tool is an open decision (CSS integration or documented waiver) — tracked in AI-DLC Inception docs, not here.
