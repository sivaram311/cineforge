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

Persistent Network Volume `ai-film-workspace` (`f0imtkpmfh`, 150 GB, `EU-RO-1`) now exists — see `docs/aidlc/INFRA.md`. Currently attached to pod `u1g5ulbsam9uwo` (A100 SXM) at `/workspace` — the pod itself has been swapped 4 times (`t3s9yfpovyi2um` RTX 4090, `f4fkrclbvqm7gi` RTX PRO 6000 Blackwell, `qviysdl1bybtav` A100 PCIe, `vuejmb09xepyyr` A100 SXM — all terminated), the volume survives each swap.

## Infra note — ComfyUI proven working, full promo delivered (pod now stopped)

ComfyUI ran on pod `u1g5ulbsam9uwo` (A100 SXM 80GB, `EU-RO-1`, currently **stopped** to control cost — replaces the terminated `vuejmb09xepyyr`, whose resume failed the same way `qviysdl1bybtav`'s did) — **real generated video clips are proven working for both LTX-2.3 and Wan 2.2, across all 4 characters**, as of 2026-08-02, see `docs/aidlc/INFRA.md` "Video promo pipeline" section. Full facts, root-cause/fixes, and security notes are in `docs/aidlc/INFRA.md`.

A real Bolt is still needed to:
1. Figure out why API-driven pod creation fails (immediate platform-side exit) while RunPod console creation works.
2. ~~Secure Jupyter access~~ **Done** — `WEB_ENABLE_AUTH=true` is now set and enforced (verified: unauthenticated `/api/kernels` now 302s to a login portal). Turned out to gate every proxied port on the pod, not just Jupyter — see `docs/aidlc/INFRA.md` for the full auth architecture and the cross-subdomain cookie nuance for browser access.

---

## Bolt 10 — Video promo pipeline (6-scene, character-driven)

**Goal:** A 6-scene / 60-second promo video (4 characters, Tamil TTS voiceover) generated via ComfyUI, orchestrated by a Python script.

**Status: DONE (2026-08-02).** `cineforge_promo_final.mp4` — 60.29s, 6 scenes, all 4 characters, Tamil VO per scene, generated end-to-end and independently verified (real frames viewed, not just format checks). See `docs/aidlc/INFRA.md` "Full 6-scene Tamil promo — DELIVERED" section for full detail: orchestration approach, the character-consistency decision (plain `LoadImage` reference, no IPAdapter/InstantID needed), and three new bugs found/fixed along the way (an `enable_gqa` torch-compatibility regression, `/opt` state getting wiped on *every* pod stop/resume not just first boot, and a doubled-subfolder path bug in the orchestration script). Scene script/prompts: `docs/aidlc/SCENES.md`. Current pod: `u1g5ulbsam9uwo` (A100 SXM 80GB, stopped to control cost). The `VAEDecode` fix was independently reconfirmed live on this fresh pod after the original pod's resume failed — see `docs/aidlc/INFRA.md` "Wan 2.2 fix reconfirmed on a fresh pod".

Done:
- Character reference images uploaded and confirmed surviving multiple pod swaps (persistent volume).
- LTX-2.3 and Wan 2.2 both proven with real, frame-content-verified clips for all 4 characters (see the Wan 2.2 noise-output bug in INFRA.md for why frame-content verification, not just container checks, is now a standing rule).
- Root-caused and fixed a whole class of workflow-conversion bugs (widget-to-input misassignment) rather than special-casing each one.
- Character-consistency decision made: plain `LoadImage` single-reference is sufficient, no IPAdapter/InstantID needed.
- Multi-scene loop built (`run_promo.py`) and run for all 6 scenes.
- Tamil TTS (`edge-tts`) wired and generated per scene.
- Final `ffmpeg` stitch (6 clips + Tamil VO overlay) wired (`stitch_promo.py`) and produces the single output file.

**Acceptance: met.** The orchestration scripts run end-to-end and produce a final stitched Tamil promo video, independently verified frame-by-frame, not just claimed.
