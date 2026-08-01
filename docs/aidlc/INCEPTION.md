# cineforge — AI-DLC Inception Charter

**Phase:** Inception (Day 1)  
**Status:** Spec / ask only — not yet functional  
**Next phase:** Construction (Bolt-sized diffs + evidence)

---

## Purpose

**cineforge** is a movie-generation pipeline that orchestrates RunPod (GPU cloud) to turn text and image prompts into video clips, then (later) assemble those clips into a longer piece.

It is for a single operator (or small crew) who wants an auditable, local-first orchestration layer over RunPod Serverless video generation — not a from-scratch GPU host. Primary integration path: RunPod's official MCP server (interactive / agent-driven) and RunPod REST API (programmatic submit / poll / retrieve).

---

## Scope for this Inception + first Construction pass

**In scope**

- Charter, tech-stack decision, architecture sketch, and ordered Bolt backlog (this doc + `BOLTS.md`)
- A minimal CLI + library skeleton that compiles / runs but does **not** yet call RunPod for real (scaffold hire; separate workstream)
- Reserved DEV ports only — no binding yet

**Explicitly out of scope for this pass**

- Web UI (future `:3401` Bolt)
- Real RunPod calls wired to live secrets
- Multi-clip stitching into a finished movie
- PREPROD / PROD deploy (F: / G:) — Operations is out of scope
- Binding to reserved ports

**Shape of the first Construction deliverable:** a working skeleton that can later be pointed at a real RunPod account; CLI + `cineforge` library module only.

---

## Tech stack decision

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Language / runtime | Python 3.11+ | RunPod ecosystem (`runpod` Python SDK, `worker-comfyui`) is Python-first; orchestration is HTTP + polling + light file I/O |
| Packaging | `pyproject.toml`, standard `pip` / `venv` | No exotic package manager |
| Package name | `cineforge` | Fixed project identity |
| Surface | CLI + library only | No web UI in Inception / first Construction |
| Layout | `src/cineforge/`, `tests/`, `docs/` (`docs/aidlc/` for AI-DLC), root `README.md`, `pyproject.toml`, `.gitignore`, `.env.example` | Machine convention for this project |

This decision is **fixed** — do not re-decide during Construction.

---

## Architecture sketch

Target flow for a movie-generation request (forward-looking; not yet implemented):

```
┌─────────────┐     prompt / job spec      ┌──────────────────┐
│  Operator   │ ─────────────────────────► │  cineforge CLI / │
│  or Agent   │     (or MCP-driven)        │  library         │
└─────────────┘                            └────────┬─────────┘
                                                    │
                    ┌───────────────────────────────┼───────────────────────────────┐
                    │                               ▼                               │
                    │  RunPod REST API          RunPod MCP server                   │
                    │  (submit / poll /         (interactive pods, endpoints,       │
                    │   retrieve)                jobs, pricing, spend)              │
                    └───────────────────────────────┬───────────────────────────────┘
                                                    │
                                                    ▼
                                    ┌───────────────────────────────┐
                                    │  RunPod Serverless endpoint   │
                                    │  ComfyUI worker / WAN 2.6     │
                                    │  T2V · I2V · T2I · ref→video  │
                                    └───────────────┬───────────────┘
                                                    │
                                      poll until COMPLETE
                                                    │
                                                    ▼
                                    ┌───────────────────────────────┐
                                    │  Output clip(s) / image URLs  │
                                    │  (or binary download)         │
                                    └───────────────┬───────────────┘
                                                    │
                                      (future Bolt)
                                                    ▼
                                    ┌───────────────────────────────┐
                                    │  Stitch clips → longer piece  │
                                    └───────────────────────────────┘
```

**Practical generation call shape**

1. Submit a job (prompt + params, or ComfyUI workflow JSON) to a RunPod Serverless endpoint  
2. Poll job status  
3. Retrieve output (video / image URLs or binary) once complete  

**WAN 2.6 (current public serverless video model on RunPod):** text-to-video, image-to-video, text-to-image, and reference-to-video for character consistency across scenes; up to ~15s clips; per-request billing (no idle cost).

---

## Auth / security note (open decision)

This machine's standing rule is centralized auth via the **Centralized Security System (CSS)** for anything beyond a public no-login static site.

A single-operator local pipeline tool can plausibly start **without** CSS during early Construction, but that is **not** a long-term assumption.

**Open decision (must be resolved before multi-user or public-facing deployment):**

- **(a)** Integrate CSS before any multi-user or public-facing deployment, **or**
- **(b)** Record an explicit documented waiver

Inception does **not** resolve this. Construction Bolts that add network-facing surfaces must revisit this decision.

---

## Secrets handling

- RunPod API keys (and any other provider keys) must **never** be committed to git
- Use environment variables only (e.g. `RUNPOD_API_KEY`)
- Root `.env.example` holds placeholder names only (`RUNPOD_API_KEY=`)
- `.gitignore` must exclude `.env`
- RunPod API MCP is local `npx @runpod/mcp-server` (needs `RUNPOD_API_KEY` in client env / `.env` — never commit the literal key); Docs MCP at `https://docs.runpod.io/mcp` is hosted read-only with no auth. Direct REST also needs keys via env. See `docs/RUNPOD-MCP-SETUP.md`

---

## Deploy topology (target, not yet real)

| Role | Drive | Ports | Status |
|------|-------|-------|--------|
| DEV | E: | `:3400` (api), `:3401` (future UI), `:3402` (future worker) | Reserved only — do not bind in Inception |
| PREPROD | F: | — | Not reserved yet |
| PROD | G: | — | Not reserved yet |
| RELEASES | H: | — | N/A for Inception |

Nothing is deployed to F: or G: during Inception. Drive roles must not be mixed.

---

## Known risks / open questions

| Topic | Note |
|-------|------|
| Cost control | Per-job billing; T2I ~$0.03/image; video cost scales with length/settings. `cineforge balance` can check account balance/spend rate on demand; budgets / dry-run / confirm-before-spend guardrails are still not built |
| GPU availability / queueing | Serverless queues can delay jobs; UX and retries TBD |
| Clip length | WAN 2.6 caps ~15s per clip — longer movies require multi-clip stitch (future) |
| Output storage / retention | Where clips land locally vs. remote URLs; retention policy TBD |
| Auth | CSS vs. documented waiver (see above) — unresolved |
| MCP vs REST | Dual path corrected: API MCP is self-hosted via `npx @runpod/mcp-server` (real key required; `.cursor/mcp.json` uses `${env:RUNPOD_API_KEY}` + `envFile` so nothing secret is committed); Docs MCP is the only hosted no-auth server (`docs.runpod.io/mcp`). Config is corrected, but connecting still needs Node 18+ and a key available to Cursor. REST client remains for scripted/CI-safe calls — see `docs/RUNPOD-MCP-SETUP.md` |
| ComfyUI workflow versioning | Workflow JSON may drift with worker image updates |

---

## Initial Bolt backlog

See **[`BOLTS.md`](./BOLTS.md)** for the ordered Construction backlog (small, reviewable-in-one-sitting units).
