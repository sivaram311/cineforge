# cineforge — Construction Bolt Backlog

Ordered list of AI-DLC Bolts for Construction. Each Bolt = one mergeable change + evidence + docs update, small enough to review in one sitting.

Evidence expectations: unit tests where noted; for paid RunPod calls, manual smoke notes only (not automated CI).

---

## Bolt 1 — Project skeleton & env contract

**Goal:** Ship a minimal `cineforge` package (`src/cineforge/`), `pyproject.toml`, `.gitignore`, `.env.example` (`RUNPOD_API_KEY=`), and a CLI entrypoint that prints version / help without calling RunPod.

**Acceptance:** `pip install -e .` succeeds; `cineforge --help` (or equivalent) runs; `.env` is gitignored; no secrets in tree.

---

## Bolt 2 — RunPod API client wrapper (mocked)

**Goal:** Library module that authenticates via `RUNPOD_API_KEY`, submits a Serverless job, polls status, and fetches the result — all against a mocked HTTP layer.

**Acceptance:** Unit tests cover submit → poll → complete and error / timeout paths; no live network in CI.

---

## Bolt 3 — CLI: submit one text-to-video job (live smoke)

**Goal:** CLI command that submits a single T2V job end-to-end against a real RunPod account using the client from Bolt 2.

**Acceptance:** Manual smoke test documented (prompt → job id → output URL/path); operator confirms spend; not wired into automated CI (costs money per call).

---

## Bolt 4 — Job status & result retrieval CLI

**Goal:** CLI commands to poll an existing job by id and download / print the output artifact location.

**Acceptance:** Operator can resume after disconnect; mocked unit tests for status mapping; live smoke optional and documented.

---

## Bolt 5 — Config & cost guardrails

**Goal:** Local config for default endpoint id, poll interval, max wait, and a confirm-before-spend (or `--yes`) gate for live generation.

**Acceptance:** Dry-run / confirm path documented; defaults live in env or config file (no secrets); README updated with cost warning.

---

## Bolt 6 — Image-to-video & reference-to-video inputs

**Goal:** Extend client + CLI to accept image / reference inputs for I2V and character-consistent reference-to-video (WAN 2.6 capabilities).

**Acceptance:** Mocked tests for payload shape; one documented live smoke per mode (optional, paid).

---

## Bolt 7 — Clip manifest for future stitch

**Goal:** Persist a simple local manifest (JSON) of completed clips (prompt, job id, path/URL, duration, order) as the handoff for a later stitch Bolt.

**Acceptance:** Manifest written after successful retrieve; schema documented in `docs/`; no actual stitch yet.

---

## Bolt 8 — Auth decision checkpoint (CSS or waiver)

**Goal:** Before any multi-user or public-facing surface (including binding `:3400` / `:3401`), record either CSS integration plan or an explicit documented waiver per Inception.

**Acceptance:** Decision written under `docs/aidlc/`; no silent no-auth assumption for network-facing deploy.

---

## Bolt 9 — Account balance check (shipped ad hoc)

**Done.** `src/cineforge/account.py` (`get_account_balance()` via RunPod GraphQL `myself`) + `cineforge balance` CLI + `tests/test_account.py` (7 mocked unit tests). Built ad hoc ahead of the ordered backlog once a real API key became available (Cost control risk in INCEPTION.md).

---

## Infra note — Network volume provisioned

Persistent Network Volume `ai-film-workspace` (`f0imtkpmfh`, 150 GB, `EU-RO-1`) now exists — see `docs/aidlc/INFRA.md`. Now attached to pod `t3s9yfpovyi2um` at `/workspace`.

## Infra note — ComfyUI live on manually-created pod

ComfyUI is live on pod `t3s9yfpovyi2um` (`mid_coffee_goldfish`, RTX 4090, `EU-RO-1`, image `ghcr.io/ai-dock/comfyui:latest-cuda`) — access via https://t3s9yfpovyi2um-8188.proxy.runpod.net/. Full facts, root-cause/fix, and security notes are in `docs/aidlc/INFRA.md`.

A real Bolt is still needed to:
1. Figure out why API-driven pod creation fails (immediate platform-side exit) while RunPod console creation works.
2. Secure Jupyter access (enable auth / `WEB_ENABLE_AUTH=true`) before this pod is used for anything beyond throwaway testing — the Jupyter proxy is currently unauthenticated despite a configured password.

---

## Bolt 10 — Video promo pipeline (6-scene, character-driven, not started)

**Goal:** A 6-scene / 60-second promo video (4 characters, Tamil TTS voiceover) generated via ComfyUI on pod `t3s9yfpovyi2um`, orchestrated by a Python script.

**Current status (see `docs/aidlc/INFRA.md` "Video promo pipeline" section for full detail):**
- Character reference images: **uploaded** to `/workspace/ComfyUI/input/characters/`.
- `ffmpeg`: present.
- Everything else — video-generation custom nodes (IPAdapter/InstantID/AnimateDiff/Wan/LTX-Video/VideoHelperSuite), the multi-GB video model weights, a real exported API-format workflow JSON, and `edge-tts`/`moviepy` in the ComfyUI venv — **not yet in place**. This is real multi-step Construction work, not a quick follow-up.

**Acceptance (not yet met):** the orchestration script runs end-to-end against this pod and produces `1min_tamil_promo_final.mp4`; each sub-step (node install, model download, workflow authoring, TTS+ffmpeg stitch) should land as its own reviewable sub-Bolt rather than one large unverified attempt, given how much this session's pod-creation and tooling troubleshooting cost in time — verify each layer before building the next.
