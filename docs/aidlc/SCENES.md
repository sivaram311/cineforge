# cineforge — 6-Scene Promo Script

**Status: DELIVERED (2026-08-02).** This script was rendered — see
`cineforge_promo_final.mp4` (60.29s, verified frame-by-frame) and
`docs/aidlc/INFRA.md`'s "Full 6-scene Tamil promo — DELIVERED" section and
`docs/aidlc/BOLTS.md` Bolt 10. Authored by the agent in the absence of a
specific creative brief (no product/brand/message was given). Theme chosen:
a cinematic "meet the crew" identity reel featuring all 4 characters, urban
night aesthetic — reuses the exact visual style already proven working in
the LTX-2.3 and Wan 2.2 pipelines (rain-slicked city streets, neon lights,
moody atmosphere), to minimize the risk of spending pod time on an untested
look. **Still editable** for a future re-render if this isn't the intended
direction — nothing below is locked in beyond what was actually generated.

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

## Orchestration plan (as executed)

1. Reused the proven per-scene generation pattern (`run_promo.py`, built on
   the LTX conversion/patch/submit approach) — parameterized character
   image, prompt, and output filename per scene, looped over the table
   above in one pod session.
2. Generated all 6 clips using **LTX-2.3** (not Wan 2.2) for the final
   deliverable: LTX produces audio+video jointly and already has a
   face-fidelity fix applied (`strength: 1.0`, `img_compression: 8`) — Wan
   2.2 remains proven-working as a secondary option but LTX was the more
   mature path for this deliverable.
3. Generated 6 Tamil VO lines via `edge-tts` (`run_promo.py`).
4. Stitched: 6 video clips + VO lines overlaid/timed per scene (VO padded
   to each scene's length, replacing LTX's own ambient audio track), via
   `ffmpeg` (`stitch_promo.py`) → single output MP4.
5. Downloaded the final stitched file and **verified actual frame content**
   (not just format) by extracting and viewing frames from all 6 scenes
   before declaring success — the standing rule established after the Wan
   2.2 noise-output bug (see `INFRA.md`). All 6 scenes confirmed real,
   coherent, character-matching video.

## Open items / assumptions made without confirmation

- No product/brand name or specific message was provided — VO lines are
  generic "journey/friendship" phrasing. Replace if there's a real message.
- Scene 5/6 "callback" framing assumes a simple narrative arc (intro →
  each character → closing) rather than a specific story beat.
- No group/multi-character-in-one-frame shots attempted — the proven
  pipeline only supports single-reference image-to-video per generation.
