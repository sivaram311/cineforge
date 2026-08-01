# cineforge — Live infrastructure log

Tracks real RunPod cloud resources this project has provisioned (not code, not Bolts). These cost money and need operator awareness.

---

## Network volumes

| Field | Value |
| --- | --- |
| Volume ID | `f0imtkpmfh` |
| Name | `ai-film-workspace` |
| Size | 150 GB |
| Data center | `EU-RO-1` |
| Attached to Pod | `t3s9yfpovyi2um` (`mid_coffee_goldfish`) at `/workspace` |
| Created via | RunPod REST API — `POST https://rest.runpod.io/v1/networkvolumes` |
| Auth | Project `RUNPOD_API_KEY` (value never stored in docs) |
| Verified | Independently confirmed via `GET /v1/networkvolumes/f0imtkpmfh` (matching fields) |

**Data center note:** Originally requested `US-KS-2`, which returned a 500 / not found / does not support network volumes error. The error response listed available data centers including `EU-RO-1`, which was used instead (matches the operator's stated fallback preference).

**MCP note:** RunPod MCP could not be used for this creation (not yet authenticated — see `docs/RUNPOD-MCP-SETUP.md`). Direct REST API was used instead and reached the same outcome.

---

## GPU Pods

| Field | Value |
| --- | --- |
| Pod ID | `t3s9yfpovyi2um` |
| Name | `mid_coffee_goldfish` |
| GPU | RTX 4090 (~24.8 GB VRAM free at verify time) |
| Data center | `EU-RO-1` |
| Image | `ghcr.io/ai-dock/comfyui:latest-cuda` |
| Network volume | `f0imtkpmfh` mounted at `/workspace` |
| Public IP | `213.173.99.34` |
| ComfyUI URL | https://t3s9yfpovyi2um-8188.proxy.runpod.net/ (RunPod `proxy.runpod.net` for HTTP ports — not direct IP:port) |
| Created via | RunPod console (manual). All prior API-driven create attempts this session failed with an immediate platform-side exit for unresolved reasons; console creation worked where the API did not. |
| Verified | `supervisorctl status comfyui` → RUNNING; internal `127.0.0.1:18188` and `:8188` → 200; external `/system_stats` → 200 with `comfyui_version` 0.29.2, `pytorch_version` 2.4.1+cu121, CUDA device `NVIDIA GeForce RTX 4090` |

### Root cause / fix (ComfyUI startup)

- **Initial symptoms:** `supervisorctl restart comfyui` spawn-erroring; `python main.py` → `ModuleNotFoundError: No module named 'sqlalchemy'`; `micromamba` not on PATH.
- **Access path for diagnosis:** SSH was unreachable (direct IP:port connection refused; `ssh.runpod.io` reachable but no SSH public key was registered on this pod, so publickey auth was rejected). Diagnosis used the container's Jupyter kernel API instead.
- **Root cause:** Supervisor was already correctly configured to use the real venv at `/opt/environments/python/comfyui` (via `/opt/ai-dock/bin/supervisor-comfyui.sh`, config at `/etc/supervisor/supervisord/conf.d/comfyui.conf`). ComfyUI was synced to `master` (`COMFYUI_BRANCH=master`), which needs newer deps (`sqlalchemy`, `alembic`, `blake3`, `comfy-aimdo==0.4.10`, `comfy-kitchen==0.2.22`, plus frontend/templates/docs packages, `av`, `simpleeval`, `aiohttp`/`yarl` bumps) that were not present in the image's venv — so supervisor's `comfyui` process stayed FATAL/spawn-error.
- **Fix:** Installed the missing packages into `/opt/environments/python/comfyui`, then `sudo supervisorctl start comfyui`.

### Key paths

| Role | Path |
| --- | --- |
| Python (ComfyUI venv) | `/opt/environments/python/comfyui/bin/python` |
| App | `/opt/ComfyUI` (symlink → `/workspace/ComfyUI`) |
| Supervisor conf | `/etc/supervisor/supervisord/conf.d/comfyui.conf` |
| Launch script | `/opt/ai-dock/bin/supervisor-comfyui.sh` |

---

## Known issues / security notes

- **SSH unavailable on this pod.** No SSH public key was registered; do not assume shell access via SSH for future sessions.
- **Jupyter is publicly reachable with no auth.** Port 8888 proxy URL: https://t3s9yfpovyi2um-8888.proxy.runpod.net/ — `WEB_ENABLE_AUTH=false`, so `/api/kernels` REST + websocket is reachable with **no authentication** from the public internet. Anyone who discovers this URL has unauthenticated code execution inside the container. A password is already set via `JUPYTER_PASSWORD` but is not enforced. **Near-term follow-up:** enable Jupyter auth (`WEB_ENABLE_AUTH=true`) or restrict network access before using this pod beyond throwaway testing.

---

## Video promo pipeline — status (6-scene, 60s character-driven promo)

A user plan calls for a 6-scene / 60-second promo (4 characters: Mathura, Siva, Akhil, Ajith) using image-to-video generation + a Tamil TTS voiceover, orchestrated by a Python script hitting the ComfyUI API. **Verified prerequisite status as of the live check below — do not assume any of this exists without re-checking, since it changes as work lands:**

| Item | Status |
| --- | --- |
| Character reference images | **Uploaded.** `/workspace/ComfyUI/input/characters/{ajith.png, akhil.jpg, mathura.jpg, siva.jpg}`, via Jupyter Contents API (base64 PUT, XSRF-token-authenticated — plain PUT alone returns 403 even with `WEB_ENABLE_AUTH=false`, since Jupyter's CSRF protection is separate from login auth). Sizes verified matching the local source files exactly. |
| Custom nodes (IPAdapter / InstantID / AnimateDiff / Wan / WanVideo / LTX-Video / VideoHelperSuite) | **Absent.** Only `ComfyUI-Manager` and `ComfyUI_essentials` are installed. None of the character-consistency or video-generation node packs exist yet — must be installed before any image-to-video generation can run. |
| Video model weights (Wan2.1/2.2, LTX-Video, AnimateDiff motion modules, IPAdapter/InstantID weights) | **Absent.** Only SD1.5 + SDXL base/refiner image checkpoints (~16GB) plus some ControlNet/VAE/upscalers are present, under `/workspace/storage/...` (symlinked into `/opt/ComfyUI/models/`). No video-generation weights exist on this pod yet. Disk is not the blocker — `/workspace` (network volume) has hundreds of TB free. |
| Workflow API JSON (e.g. `film_scene_api.json`) | **Does not exist.** Stock ComfyUI blueprints (Wan 2.2, LTX-2.3, Merge Videos, etc.) ship with the image but are UI templates, not an exported API-format workflow wired for this project's 6-scene pipeline. One needs to be built (normally: assemble in the ComfyUI web UI once the right nodes/models are installed, then export via Dev Mode "Save (API Format)"). |
| `edge-tts`, `moviepy` (Python deps for the orchestration script) | **In progress** — install attempted via the ComfyUI venv (`/opt/environments/python/comfyui`); see session notes, not yet independently re-confirmed present as of this doc update. Re-check via `ls /opt/environments/python/comfyui/lib/python3.10/site-packages \| grep -iE 'edge\|moviepy'` before relying on the orchestration script. |
| `ffmpeg` / `ffprobe` | **Present** (`/usr/bin/ffmpeg` 4.4.2, confirmed working). |
| `micromamba` | **Not installed / not on PATH.** Do not use `micromamba run -n comfyui ...` as in some example commands — use `/opt/environments/python/comfyui/bin/python` (or `pip`) directly instead. |

**Bottom line:** ComfyUI itself is healthy and reachable, and the character images are staged, but the actual image-to-video generation capability (nodes + models + a real workflow) does not exist on this pod yet — that's real, multi-step Construction work (installing node packs, downloading multi-GB model weights, building/exporting a working API workflow), not a quick follow-up. Do not attempt to run the orchestration script against this pod until those are in place.

**Access method note (for whoever picks this up next):** SSH does not work on this pod (see above). All diagnosis and fixes so far went through the unauthenticated Jupyter kernel API on port 8888 — either via a proper client library (recommended; a hand-rolled raw WebSocket client is easy to get subtly wrong around multi-frame message reassembly, which cost real time this session) or via `cursor-agent`, which has reliably driven this pod's Jupyter kernel for both the ComfyUI supervisor fix and Python package installs.
