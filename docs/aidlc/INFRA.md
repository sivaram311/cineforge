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
| Attached to Pod (current) | `vuejmb09xepyyr` (`cineforge-comfyui-a100sxm`, A100 SXM) at `/workspace` — previously `t3s9yfpovyi2um` (RTX 4090), `f4fkrclbvqm7gi` (RTX PRO 6000 Blackwell), and `qviysdl1bybtav` (A100 PCIe), all terminated, same volume reattached each time |
| Created via | RunPod REST API — `POST https://rest.runpod.io/v1/networkvolumes` |
| Auth | Project `RUNPOD_API_KEY` (value never stored in docs) |
| Verified | Independently confirmed via `GET /v1/networkvolumes/f0imtkpmfh` (matching fields) |

**Data center note:** Originally requested `US-KS-2`, which returned a 500 / not found / does not support network volumes error. The error response listed available data centers including `EU-RO-1`, which was used instead (matches the operator's stated fallback preference).

**MCP note:** RunPod MCP could not be used for this creation (not yet authenticated — see `docs/RUNPOD-MCP-SETUP.md`). Direct REST API was used instead and reached the same outcome.

---

## GPU Pods

**Current pod (stopped, not billing):**

| Field | Value |
| --- | --- |
| Pod ID | `vuejmb09xepyyr` |
| Name | `cineforge-comfyui-a100sxm` |
| GPU | **NVIDIA A100-SXM4-80GB** (~78.85 GB VRAM free at last verify) |
| Data center | `EU-RO-1` |
| Image | `ghcr.io/ai-dock/comfyui:latest` |
| Network volume | `f0imtkpmfh` mounted at `/workspace` |
| SSH | Working when running (rescue key `cineforge-rescue`); port mapping changes on every resume — always fetch fresh via `GET /v2/pods` |
| Cost | $1.49/hr while running — currently **stopped** (`desiredStatus: EXITED`, stopped 2026-08-02 after the 6-scene promo delivery to control cost), not billing |
| Verified | Internal (SSH) `127.0.0.1:18188/system_stats` → 200, `comfyui_version` 0.29.0, `pytorch_version` 2.4.1+cu121, CUDA device `NVIDIA A100-SXM4-80GB`. `torch.cuda.get_device_capability(0)` → `(8, 0)` (`sm_80`) — explicitly supported by this PyTorch build, unlike the Blackwell pod below. |
| Resuming | Every stop/resume on this pod has wiped `/opt` state (symlink + venv packages) — see "Full 6-scene Tamil promo" section below for the standing post-resume checklist before submitting any job. |

**Prior pods this session (all retired):**

| Pod ID | GPU | Outcome |
| --- | --- | --- |
| `t3s9yfpovyi2um` | RTX 4090 (24GB, `sm_89`) | Terminated. ComfyUI ran fine, but the LTX-2.3 22B model + Gemma 12B text encoder together (~34GB+) OOM'd during actual sampling even after CPU-offloading the text encoder — genuinely doesn't fit in 24GB for this pipeline. |
| `f4fkrclbvqm7gi` | RTX PRO 6000 Blackwell Workstation Edition (96–98GB, `sm_120`) | Terminated. Plenty of VRAM, but **`sm_120` (Blackwell) is not in this image's PyTorch 2.4.1 supported-architecture list** (`sm_50` through `sm_90` only) — every GPU op failed with `CUDA error: no kernel image is available for execution on the device`. Would need a PyTorch upgrade (2.6+/CUDA 12.4+) to use this generation of card with the stock image; not attempted. |
| `qviysdl1bybtav` | A100 80GB PCIe (`sm_80`) | Terminated. Fully worked (this is where the first LTX-2.3 and face-fidelity-fix clips were generated) — stopped for cost control between sessions, but **failed to resume**: `GraphQL podResume` returned "not enough free GPUs on the host machine to start this pod" (the physical host's A100 had been reallocated elsewhere while stopped). Terminated and recreated as `vuejmb09xepyyr` (A100 SXM variant, different capacity pool) since plain PCIe A100 had no capacity at recreate time either. **Lesson:** RunPod's "stop" (vs "terminate") only reliably resumes if the same physical host still has the GPU free — not guaranteed, especially after a gap. |

**Lesson for future GPU choices on this image:** stick to Ampere/Ada-or-older architectures (`sm_80` A100, `sm_86`, `sm_89` RTX 4090/L40S/RTX 6000 Ada, `sm_90` H100) unless the image's PyTorch is deliberately upgraded first. Newer Blackwell-generation cards (`sm_120`, e.g. RTX PRO 6000 Blackwell, RTX 50-series) will not run any CUDA op on this stock `ghcr.io/ai-dock/comfyui` image.

### External browser access now requires portal login

After enabling `WEB_ENABLE_AUTH=true` (see Known issues / security notes), ai-dock's Caddy layer gates **every** proxied HTTP port on this pod, not just Jupyter — including ComfyUI's `:8188`. Hitting `https://t3s9yfpovyi2um-8188.proxy.runpod.net/` directly now 302s to a login portal on a **different** port (`:1111`, `serviceportal` service): `https://t3s9yfpovyi2um-1111.proxy.runpod.net/login`, credentials `WEB_USER`/`WEB_PASSWORD` from pod env.

**Important nuance:** the auth cookie set after logging in at the `:1111` portal is scoped to that port's own subdomain and does **not** carry over to `:8188`'s subdomain (they're distinct hostnames under `proxy.runpod.net`, not the same domain on different ports) — logging in through the portal once does not automatically unlock the ComfyUI UI in the same browser session in a single step; RunPod embeds this the way the portal is meant to be used (users normally reach ComfyUI's UI by clicking through from the portal's own service links, rather than pasting the `:8188` URL directly). If pasting the ComfyUI URL directly still shows the portal/login page after logging in, that's expected behavior given this cross-subdomain cookie scoping, not a bug.

This does **not** block the actual generation pipeline — the orchestration script runs from inside the pod (SSH/Jupyter kernel) and talks to ComfyUI via `127.0.0.1:8188`, which bypasses the external Caddy auth layer entirely.

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

- **RESOLVED — Jupyter unauthenticated RCE.** Originally, Jupyter (port 8888) had `WEB_ENABLE_AUTH=false`, making `/api/kernels` (REST + websocket code execution) reachable with no authentication from the public internet. **Fixed**: `WEB_ENABLE_AUTH=true` is now set and enforced via ai-dock's Caddy layer, verified by an unauthenticated `GET /api/kernels` returning a `302` redirect to a login portal instead of live kernel data. This turned out to gate **every** proxied HTTP port on the pod (including ComfyUI's `:8188`), not just Jupyter — see "External browser access now requires portal login" above.
- **SSH is now available on this pod** (was previously unavailable — no key had been registered). A rescue SSH keypair (public key labeled `cineforge-rescue`) was added to the pod's `PUBLIC_KEY` during the auth-fix recovery. The matching private key lives only in local session scratch files, not in this git repo. Port mapping for SSH changes on pod restart — always fetch the current mapping via `GET https://api.runpod.io/v2/pods` rather than assuming a previously-seen port number is still correct.
- **Side effect of the auth fix:** enabling it required a pod stop/resume cycle (to get SSH working for recovery), which reset the container's local disk (`/opt/...`) and wiped ComfyUI's earlier pip-installed dependency fixes. They were confirmed still needed and were not required to be reinstalled a second time in the end — ComfyUI came back RUNNING after the resume. Worth knowing: **anything installed under `/opt/` does not survive a pod stop/resume** — only `/workspace` (the persistent network volume) does. Character images and any future generated output are safe; ad hoc `pip install`s into `/opt/environments/...` are not, if the pod is ever stopped/resumed again.

---

## Video promo pipeline — status (6-scene, 60s character-driven promo)

A user plan calls for a 6-scene / 60-second promo (4 characters: Mathura, Siva, Akhil, Ajith) using image-to-video generation + a Tamil TTS voiceover, orchestrated by a Python script hitting the ComfyUI API.

### Wan 2.2 pipeline also proven — all 4 characters (2026-08-02, second pod)

**Two model families now both work on this project's pod setup.** After the LTX-2.3 milestone below, also installed **Wan 2.2** (dual-expert high/low-noise 14B architecture) on a fresh A100-SXM pod (`vuejmb09xepyyr`), and generated **one real clip per character** — all 4 correct h264/512x320, ~3s each, no audio track (Wan 2.2 is video-only, unlike LTX's audio+video pipeline).

**CRITICAL bug found and fixed (2026-08-02, later same day): first-round clips were pure noise, not real video.** The initial "all 4 verified" claim only checked container/format validity (`ffprobe` codec/resolution/duration, file size) — it never inspected actual frame content. The user caught this ("nothing other than colour") and asked for a deep dive; extracting real PNG frames via `ffmpeg` from all 4 first-round clips confirmed they were pure decoded Gaussian noise (TV-static), not video. **Root cause:** `VAEDecode`'s `samples` input was wired to the stage-1 `KSamplerAdvanced` output (`add_noise: enable`, only steps 0→2 of 4, starting from raw noise) instead of the stage-2 output (`add_noise: disable`, steps 2→end, the actual final refinement). Stage 2 ran and produced a correctly denoised latent, but its output was never consumed — the barely-denoised stage-1 latent got decoded instead. The two-stage *handoff* wiring (stage1→stage2 latent chain) was correct; only the final `VAEDecode` was pointed at the wrong stage. Fixed in the conversion script by forcing `VAEDecode.samples` to always point at `[ksampler_ids[-1], 0]` (the last/final stage) rather than trusting the raw blueprint link. **Re-verified by actually viewing extracted frames** (not just format checks) for all 4 characters after the fix — real, coherent, character-matching video confirmed in every case. Lesson: format/container validity is necessary but not sufficient — visually inspect (or statistically check pixel variance of) actual decoded frames before claiming a generation pipeline works.

**Setup notes for next time:**
- This pod's `/opt/ComfyUI` was a **separate, non-symlinked, outdated (2024-09-05) install** by default — none of the persistent-volume fixes or models were visible to it until manually replaced with a symlink to `/workspace/ComfyUI`. Always check `readlink -f /opt/ComfyUI` on a new pod before assuming the established symlink pattern holds.
- `/workspace/ComfyUI` needed a `git checkout master && git pull` to get native `WanImageToVideo` support (the pinned `v0.29.2` tag doesn't have it), plus `pip install -r requirements.txt` for the newer frontend/comfy-kitchen packages that revision expects.
- Wan model files (`Comfy-Org/Wan_2.2_ComfyUI_Repackaged` on HuggingFace): `umt5_xxl_fp8_e4m3fn_scaled.safetensors` (text encoder), `wan_2.1_vae.safetensors` (VAE), `wan2.2_i2v_{high,low}_noise_14B_fp8_scaled.safetensors` (dual UNETs, ~14GB each), `wan2.2_i2v_lightx2v_4steps_lora_v1_{high,low}_noise.safetensors` (4-step distilled LoRAs) — ~34GB total, all confirmed by exact byte size, not assumed.
- The `Image to Video (Wan 2.2)` blueprint conversion hit several new instances of the same widget-misassignment bug class (this time: `CLIPLoader`'s `type`/`device` fields, `UNETLoader`'s `weight_dtype`, `WanImageToVideo`'s `batch_size`/`clip_vision_output` both getting a stray `640`), the two-stage `KSamplerAdvanced` handoff needing full respecification (fixed by confirming each node's real output slot via `object_info` rather than guessing), and the `VAEDecode`-points-at-wrong-stage bug described above (the actual root cause of the noise output, found last because it silently produced a valid-looking file rather than an error).
- **RunPod stop/resume lesson learned the hard way:** stopping (not terminating) a pod can fail to resume if the physical host's GPU gets reallocated — hit this on the first A100 pod, had to terminate and create a fresh one. Network volume survives regardless; only the pod itself is at risk.

### First real test clip generated (2026-08-02, LTX-2.3)

**Success, independently verified — not just a claimed result.** Using the `Image to Video (LTX-2.3)` blueprint (native LTX support, no extra custom nodes needed) on the A100 pod, with Siva's reference image and a simple test prompt:

| Field | Value |
| --- | --- |
| Output | `siva_test_i2v_00001_.mp4` in `/workspace/ComfyUI/output/cineforge/` |
| Verified via | `ls -la` (real 1,703,841-byte file) + `ffprobe` (valid ISO Media MP4, h264 512×320 video, aac audio, 26.04s) |
| Settings used | 512×320, ~26s duration, prompt: "cinematic shot of a man standing in rain-slicked city streets at night, neon lights, moody atmosphere" |
| Checkpoint | `ltx-2.3-22b-dev-fp8.safetensors` + `ltx-2.3-22b-distilled-lora-384.safetensors` LoRA + `gemma_3_12B_it_fp4_mixed.safetensors` text encoder + `ltx-2.3-spatial-upscaler-x2-1.1.safetensors` upscaler |
| GPU usage | Peaked ~100% utilization, ~60.5GB VRAM (of 80GB available) |

**How the workflow was built:** ComfyUI's stock blueprints (`Text to Video (LTX-2.3).json`, `Image to Video (LTX-2.3).json`, etc.) are UI-format files using ComfyUI's subgraph feature — the real node graph lives nested under `definitions.subgraphs[0]`, not the top-level `nodes`/`links` arrays (those just hold a single wrapper/reference node). A custom Python converter was written (`/workspace/convert_workflow.py` pattern, not committed to the repo — recreate if needed) that:
1. Extracts the subgraph's real node/link list.
2. Resolves links by their explicit `link_id` (not by re-deriving slot-index matches — more robust).
3. Bypasses pure-passthrough `Reroute` nodes by tracing back to their true upstream origin.
4. Fetches each node type's live `object_info` schema from the running ComfyUI server to correctly map `widgets_values` positions to named inputs.

**Real bugs found in that conversion approach (not blueprint bugs — conversion-script bugs), now understood and auto-fixed:** for nodes with multiple widgets, the positional widget-to-input-name mapping sometimes misaligns (schema enumeration order ≠ actual UI widget render order), causing values to land in the wrong field. Concretely hit and fixed: `batch_size` getting a duration/fps value instead of `1`, `device` getting a filename instead of `default`, `strength_model` getting a filename instead of a float, `scale_method` getting a resolution number instead of a valid option string, `bit_depth` getting an fps value instead of a valid 8–10 range value. A generic post-conversion fixup pass now catches this whole bug class by type-checking known problem fields rather than trusting the positional mapping blindly.

**Also learned:** the `Text to Video (LTX-2.3)` blueprint specifically (as opposed to `Image to Video`) has a genuine internal AV-latent shape inconsistency when run standalone outside its original larger-graph context (video_latent and audio_latent paths didn't align even with correct, consistent parameters) — not yet root-caused, worked around by switching to the `Image to Video` blueprint instead, which worked cleanly. If picking this back up, don't assume `Text to Video` is safe to use as-is.

### Face-fidelity fix (2026-08-02, second generation)

The first clip's facial likeness didn't match the source photo closely enough. Root cause: the blueprint uses a **two-pass** pipeline (a base-resolution pass, then an upscale/refine pass), and the two `LTXVImgToVideoInplace` conditioning nodes had **mismatched strength** — the base pass was `strength: 0.7` while the refine pass was `strength: 1.0`. Since the refine pass builds on whatever the base pass already produced, a weaker base-pass anchor meant the identity had already drifted before refinement ever saw it — the higher refine-pass strength couldn't recover detail that was never there.

**Fix applied:** raised the base-pass (`LTXVImgToVideoInplace`, node id varies by blueprint — the one feeding the *non-upscaled* `EmptyLTXVLatentVideo` path) `strength` from `0.7` to `1.0` to match the refine pass, and reduced `LTXVPreprocess.img_compression` from `18` to `8` (less lossy compression of the source image before it enters the pipeline, preserving more facial detail). Regenerated `siva_test_i2v_00002_.mp4` (1,876,953 bytes, same valid h264+aac/512×320/26s format) — independently verified via `ffprobe`, not just claimed.

**For future scenes:** apply the same `strength: 1.0` on both `LTXVImgToVideoInplace` nodes and `img_compression: 8` (or lower) by default, rather than trusting the blueprint's own stock defaults for identity-sensitive shots.

### Full 6-scene Tamil promo — DELIVERED (2026-08-02)

**Status: complete.** `cineforge_promo_final.mp4` — 60.29s, h264 512×320 + AAC audio, 6 scenes × ~10s, all 4 characters, Tamil VO per scene. Scene script/prompts in `docs/aidlc/SCENES.md` (drafted by the agent — no product/brand brief existed; theme is a generic "meet the crew" identity reel reusing the already-proven visual style). Downloaded to `test_output/cineforge_promo_final.mp4` (gitignored, local only). **Verified by extracting and viewing actual frames from all 6 scenes** (not just format checks) — every scene shows real, coherent, character-matching video.

Orchestration: `run_promo.py` (loops the proven LTX-2.3 conversion/patch/submit pattern across all 6 scenes + generates Tamil VO via `edge-tts` per scene) and `stitch_promo.py` (mux each scene's video with its own VO padded to scene length via `ffmpeg apad`, replacing LTX's own ambient audio track, then concat all 6). Neither script is committed to the repo (scratch-path convention established earlier in this project) — recreate from this description if needed.

**Character-consistency nodes (IPAdapter/InstantID):** deliberately not used. The plain `LoadImage` single-reference approach already proven for individual test clips produced correct, recognizable likeness across all 6 scenes without added complexity.

**Three new bugs hit and fixed during this run, none previously seen:**

1. **`enable_gqa` regression on the Gemma text-encoder path.** The manual `comfy/ops.py` patch from earlier in this session (torch 2.4.1 doesn't support the `enable_gqa` kwarg) had been dropped via `git stash drop` after confirming the `master` branch "already handles it" — but that confirmation only covered the Wan 2.2 codepath, not the LTX/Gemma text-encoder attention codepath, which crashed identically once real scene generation (not just Wan testing) resumed. **Also**: the branch's own built-in GQA handling only strips `enable_gqa` when `attn_mask is not None and not is_nvidia()` — on an NVIDIA GPU with no attn_mask, it left the kwarg untouched, then later logic still passed it straight to `torch.nn.functional.scaled_dot_product_attention`, which doesn't recognize the parameter *name* at all on torch < 2.5 (raises `TypeError: unexpected keyword argument`, regardless of value). Re-patched `comfy/ops.py`: strip `enable_gqa` via `kwargs.pop(...)` (not `kwargs["enable_gqa"] = False` — setting it to `False` still leaves the *key* present, which torch < 2.5 still rejects by name) whenever `torch.__version__ < (2, 5)`, independent of the nvidia/attn_mask branching. **Lesson: a manual compatibility patch that gets "confirmed redundant" for one codepath may still be load-bearing for a different codepath through the same shared file — verify against the actual failing call site, not just the one you were testing at the time.**
2. **Stop/resume wipes `/opt` state every time, not just once.** This pod's own first stop→resume cycle (after the earlier Wan fix was pushed) reproduced the *exact* original fresh-pod problem: `/opt/ComfyUI` reverted to a separate, empty, non-symlinked install, and the `comfyui` venv lost `sqlalchemy`/`edge-tts`/etc. again. This is not a one-time fresh-pod quirk — it happens on **every** resume. Re-applied the same fix (symlink + `pip install -r requirements.txt` + reinstall the venv package list) — now confirmed as a standing step required after every stop/resume, not just pod creation.
3. **Doubled output subfolder in `run_promo.py`'s path construction.** `OUT_DIR` was set to `.../output/cineforge` while `filename_prefix` (e.g. `"cineforge/scene1_siva"`) also creates a `cineforge` subfolder under ComfyUI's base output dir — real files landed at `.../output/cineforge/scene1_*.mp4`, but the manifest recorded `.../output/cineforge/cineforge/scene1_*.mp4`. Caught by verifying the files actually existed at the claimed path before handing them to the stitch step, not by trusting the script's own success log. Fixed by a one-line `sed` correction on `manifest.json` rather than re-running generation.

**For next time (standing checklist after any pod stop/resume, not just first boot):**
1. `readlink -f /opt/ComfyUI` — if not `/workspace/ComfyUI`, redo the symlink (`rm -rf /opt/ComfyUI && ln -s /workspace/ComfyUI /opt/ComfyUI`).
2. Reinstall into the `comfyui` venv: `sqlalchemy alembic blake3 comfy-aimdo==0.4.10 comfy-kitchen==0.2.22 av simpleeval edge-tts moviepy`, plus `pip install -r /workspace/ComfyUI/requirements.txt` for the frontend/comfy-kitchen version bump `master` expects.
3. Re-verify the `enable_gqa` patch is present in `/workspace/ComfyUI/comfy/ops.py` (it's on the persistent volume, so it *should* survive — but confirm, don't assume, given how many other things silently didn't).
4. `supervisorctl restart comfyui`, then poll `/object_info/LoadImage` until 200 before submitting any job.

**Access method note:** SSH works on the current pod (rescue key `cineforge-rescue`, port mapping changes on restart — always fetch fresh via `GET /v2/pods`). Prefer SSH over Jupyter's kernel API now that Jupyter requires authentication too.
