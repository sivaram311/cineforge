# cineforge

cineforge is a movie-generation pipeline that orchestrates [RunPod](https://www.runpod.io/) (GPU cloud) to turn text and image prompts into video clips, eventually assembled into a longer piece. It uses RunPod's official MCP server and REST API — not a from-scratch GPU host — with ComfyUI / WAN 2.6 Serverless endpoints for generation compute.

**Current status: Inception.** The project is not yet functional. Spec and backlog only; no live RunPod wiring in this phase.

## Docs

- **[AI-DLC Inception charter](docs/aidlc/INCEPTION.md)** — purpose, scope, stack, architecture sketch, risks
- **[Construction Bolt backlog](docs/aidlc/BOLTS.md)** — ordered, reviewable units of work

## Getting started

1. `pip install -e .`
2. Copy `.env.example` to `.env` and fill in `RUNPOD_API_KEY=` (and `RUNPOD_ENDPOINT_ID=` if using `generate`)
3. Run `cineforge balance` or `cineforge generate --prompt "..."`

Do not commit secrets. Use `.env` locally (gitignored); `.env.example` lists placeholder names only.
