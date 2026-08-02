# cineforge — 6-Scene Promo Script (draft)

**Status:** Draft, authored by the agent in the absence of a specific creative
brief (no product/brand/message was given). Theme chosen: a cinematic
"meet the crew" identity reel featuring all 4 characters, urban night
aesthetic — reuses the exact visual style already proven working in the
LTX-2.3 and Wan 2.2 pipelines (rain-slicked city streets, neon lights,
moody atmosphere), to minimize the risk of spending pod time on an
untested look. **Editable** — swap any scene's prompt or VO line before
the final render if this isn't the intended direction.

Total target length: **~60s** across 6 scenes (~10s each). Generation
approach: proven single-reference `LoadImage` → LTX-2.3 image-to-video
(no IPAdapter/InstantID) — the existing test clips already show correct,
recognizable likeness without it, and adding a character-consistency node
now would be new untested surface area for a fixed-scope deliverable.

| # | Character | Visual prompt (English, feeds ComfyUI) | Tamil VO line (feeds edge-tts) |
|---|-----------|------------------------------------------|----------------------------------|
| 1 | Siva | Cinematic shot of a man standing in rain-slicked city streets at night, neon lights, moody atmosphere, establishing shot | இது நம் கதை தொடங்கும் இடம் |
| 2 | Mathura | Cinematic close-up portrait shot, warm neon backlight, confident smile, city night backdrop softly blurred | ஒவ்வொரு பயணமும் ஒரு நம்பிக்கையுடன் தொடங்குகிறது |
| 3 | Akhil | Cinematic shot walking through a busy night market street, colorful lights reflecting on wet pavement | நண்பர்கள் சேர்ந்தால் எதுவும் சாத்தியமே |
| 4 | Ajith | Cinematic shot standing near a glowing shopfront at night, relaxed confident pose, neon signage in background | ஒவ்வொரு படியும் நம்மை முன்னோக்கி இட்டுச் செல்கிறது |
| 5 | Siva + callback | Cinematic wide shot of the same street from scene 1, now busier, warmer lighting, forward motion | இது வெறும் ஆரம்பம் தான் |
| 6 | Mathura (closing) | Cinematic final shot, turning toward camera, confident smile, city lights bokeh background, logo-card-ready empty space at bottom | நன்றி - இதுவே நம் கதை |

## Orchestration plan

1. Reuse the proven per-scene generation pattern (`wan_convert_patch_submit.py` /
   the LTX equivalent) — parameterize character image, prompt, and output
   filename per scene, loop over the table above in one pod session.
2. Generate all 6 clips using **LTX-2.3** (not Wan 2.2) for the final
   deliverable: LTX produces audio+video jointly and already has a
   face-fidelity fix applied (`strength: 1.0`, `img_compression: 8`) — Wan
   2.2 remains proven-working as a secondary option but LTX is the more
   mature path for this deliverable.
3. Generate 6 Tamil VO lines via `edge-tts` (already installed on the pod).
4. Stitch: 6 video clips concatenated in order + VO lines overlaid/timed
   per scene, via `ffmpeg` (already installed on the pod) → single output
   MP4.
5. Download final stitched file, verify **actual frame content** (not just
   format) before declaring success — this is now a standing rule after
   the Wan 2.2 noise-output bug (see `INFRA.md`).

## Open items / assumptions made without confirmation

- No product/brand name or specific message was provided — VO lines are
  generic "journey/friendship" phrasing. Replace if there's a real message.
- Scene 5/6 "callback" framing assumes a simple narrative arc (intro →
  each character → closing) rather than a specific story beat.
- No group/multi-character-in-one-frame shots attempted — the proven
  pipeline only supports single-reference image-to-video per generation.
