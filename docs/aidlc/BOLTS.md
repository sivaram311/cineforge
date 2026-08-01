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
