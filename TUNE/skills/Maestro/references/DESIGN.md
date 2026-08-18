# MAESTRO — Design 101

Offline Python POC for analyzing a ~30-second violin scale video using audio + vision models, with a VLM as the narrator of computed metrics.

## 1. Capability map

| Lane | Capability | Off-the-shelf option | Notes |
|---|---|---|---|
| Audio | Monophonic pitch (f0) | **CREPE** (DL, accurate), librosa pYIN (fast) | CREPE handles vibrato well |
| Audio | Note onset/segmentation | librosa `onset_detect`, **Basic Pitch** (Spotify) | Basic Pitch also outputs MIDI notes |
| Audio | Score alignment | librosa DTW vs. synthesized reference scale | No model — DTW against a `fluidsynth`-rendered template |
| Audio | Dynamics / timbre | librosa RMS, spectral centroid | Classical DSP, no model |
| Audio | Vibrato rate/depth | derived from CREPE f0 (FFT of detrended pitch) | No model |
| Audio | Audio-language description | **Qwen2-Audio**, SALMONN, Qwen2.5-Omni | Optional — only if you want raw "tone quality" prose |
| Vision | Instrument/bow segmentation | **SAM 2** (video-native, mask propagation), **SAM 3** (text prompts built-in) | SAM2 is the workhorse — prompt frame 0, propagate |
| Vision | Open-vocab detection (seed SAM) | **GroundingDINO**, YOLO-World | Use text "violin", "bow", "left hand" → boxes → SAM |
| Vision | Body pose | **MediaPipe Pose** (CPU), RTMPose, ViTPose | MediaPipe is plenty for posture angles |
| Vision | Hand keypoints (21/hand) | **MediaPipe Hands**, HandRefiner | Critical for left-hand fingering geometry |
| Vision | Point tracking (bow tip, frog) | **CoTracker3**, TAPIR | More robust through occlusion than raw SAM centroids |
| Vision | Generic frame features | **DINOv3** | Use for keyframe clustering / phase segmentation |
| Vision | Frame/video VLM | **Qwen2.5-VL** (3B/7B/32B), InternVL3, Moondream2 (small) | The narrator, not the judge |
| Fusion | Time-aligned metric join | pandas + frame timestamps | Plain code |
| Synthesis | Coaching report | VLM with metrics-in-prompt, or local LLM (Qwen2.5-7B-Instruct) | Ground the prose in numbers |

## 2. Pipeline

```
input.mp4 (30s)
   │  ffmpeg → audio.wav (44.1k mono) + frames (10–30 fps + container timestamps)
   │
   ├── AUDIO LANE ──────────────────────────────────────────
   │     CREPE → f0(t)
   │     librosa onset → note boundaries
   │     DTW(f0, synth(scale_name)) → note labels [C4, D4, E4,…]
   │     derive: cents_error, vibrato, attack_consistency, dynamics
   │     → per_note_audio.json
   │
   ├── VISION LANE ─────────────────────────────────────────
   │     GroundingDINO("violin","bow","left hand") on frame 0
   │     SAM2 mask propagation → per-frame masks
   │     MediaPipe Pose + Hands → keypoints
   │     CoTracker3 on {bow tip, frog, scroll, bridge corners}
   │     derive: bow_angle_to_bridge, contact_point_along_string,
   │             bow_speed, bow_distribution, posture_angles
   │     → per_frame_vision.json
   │
   ├── FUSION ──────────────────────────────────────────────
   │     join on timestamp; aggregate vision metrics per note window
   │     pick keyframes: each note onset + N worst-intonation moments
   │     → report_bundle = {metrics_table, keyframes[], plots[]}
   │
   └── SYNTHESIS ───────────────────────────────────────────
         Qwen2.5-VL(report_bundle, prompt="narrate, don't judge")
         → report.md (per-note callouts + overall summary)
```

## 3. Capability gaps and how to fill them

1. **No "violin technique" model exists.** Bow-perpendicular-to-bridge, contact point, bow distribution — none of these are pretrained tasks.
   **Fill:** geometric heuristics on top of SAM masks + pose keypoints. This is the custom code that makes the POC interesting; it's also where most of the work lives.

2. **VLMs hallucinate violin specifics.** Don't ask Qwen-VL "is the bow straight?" — it'll guess.
   **Fill:** compute the angle yourself, hand the VLM the *number* and ask it to write the sentence. VLM = narrator, DSP/CV = judge.

3. **Scale identity is ambiguous from pitch alone** (chicken-and-egg with intonation eval).
   **Fill:** make `--scale "G major 2 oct"` a CLI arg for the POC. Auto-detection is a v2 problem.

4. **Bowing direction (up-bow vs down-bow).** No off-the-shelf model.
   **Fill:** sign of bow-tip velocity along the bow's long axis (from CoTracker trajectory). 5 lines of math.

5. **String identification (which string is being played).** Audio gives you the pitch but not which string produced it (G3 on D-string vs. G3 on G-string sound different but are ambiguous to a generic pitch tracker).
   **Fill:** vision side — left-hand position relative to fingerboard tells you. Or just defer; a scale POC usually stays on adjacent strings predictably.

6. **Compute budget.** Per-frame SAM on 900 frames is slow.
   **Fill:** SAM2 mask propagation (prompt once, propagate) instead of per-frame SAM. Drop vision FPS to 10. Run audio lane in parallel — it's CPU-bound and fast.

7. **Audio-video sync.** Container metadata gives you PTS; don't assume `frame_idx / fps`.
   **Fill:** read timestamps from `pyav` or ffprobe.

8. **Coaching ground truth for evaluation.** You'll have no way to know if the report is *good*.
   **Fill (POC scope):** record a clip yourself with a deliberate flaw (sliding contact point, one flat note) and check the report catches it. That's the POC's success criterion.

## 4. v0 — what to actually build first

Strip the architecture to its spine:

- ffmpeg + CREPE + librosa onset → per-note pitch error, tempo curve
- SAM2 (single prompt on frame 0) for `bow` only → bow angle + speed
- MediaPipe Pose for posture
- Qwen2.5-VL-7B with the metrics table + 6 keyframes → markdown report

~400 lines, runs on one GPU, exercises the full pipeline. SAM3, DINOv3, CoTracker, GroundingDINO get added when a specific failure mode demands them — not upfront.
