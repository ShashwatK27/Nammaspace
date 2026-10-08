# Smartphone Capture SOP — NammaSpace

A reproducible **Standard Operating Procedure** for capturing an indoor space with
an ordinary smartphone (no LiDAR required) so that it reconstructs reliably into a
photorealistic 3D Gaussian-splat twin. Written so a non-technical teammate can
follow it and get a usable capture on the first try.

> **Why an SOP matters:** reconstruction quality is set at capture time. Garbage in →
> no amount of training fixes it. This SOP is **data-driven** — every rule below
> traces to a failure we actually hit and fixed (see *Empirical validation*).

---

## 0. Principles (the "why")
Structure-from-Motion + splatting needs, for every surface you want in the twin:
1. **Multiple viewpoints** of that surface (≥3 angles) — one pass gives zero depth.
2. **High overlap** between consecutive frames (60–80%).
3. **Sharp, consistently-exposed** frames (no motion blur, no flicker).
4. **Texture/parallax** — featureless walls, mirrors and glass are the enemies.

Everything below serves those four.

---

## 1. Pre-capture checklist (2 minutes, do every time)
- [ ] **Resolution 1080p or 4K.** Phone's native camera app. *(Our first try was a
      WhatsApp-shared clip silently recompressed to 848×478 → it reconstructed poorly.
      See §6 for transfer.)*
- [ ] **Lock exposure & focus (AE/AF lock)** — tap-and-hold on a mid-brightness
      surface until it locks. Prevents frame-to-frame brightness flicker and refocus blur.
- [ ] **Turn on all lights; open or fully close curtains** — bright, even, diffuse
      light. Avoid blown-out windows and harsh moving shadows.
- [ ] **Tidy the scene** — remove or accept moving elements (people, pets). Moving
      objects create ghost artifacts.
- [ ] **(For Round 2 metric scale)** place 1–3 **printed ArUco markers** of known
      size flat in the scene (floor/table), visible in several frames.
- [ ] **30 GB free + battery > 50%.** A 3-min 4K clip is ~1.5 GB.

## 2. Camera settings
| Setting | Value | Why |
|---|---|---|
| Mode | **Video** | steadier overlap than burst photos |
| Resolution | **1080p min, 4K preferred** | detail = model fidelity |
| Frame rate | 30–60 fps | we sample 2–4 fps later |
| Exposure/Focus | **Locked** | no flicker / refocus blur |
| Stabilization | On (standard) | avoid heavy "action/warp" modes |
| Orientation | Either, **kept consistent** | don't rotate phone mid-capture |

## 3. Capture procedure (the walk)
- **Speed:** slow, steady walk. **Smooth turns only** — never whip the phone around
  (abrupt motion = blur that breaks matching).
- **Pattern:** walk slowly **along each wall**, then **cross through the centre**, then
  **loop back to where you started** (loop closure helps alignment lock).
- **Cover every surface from ≥3 angles**, with **60–80% overlap** between views.
- **Three heights — this is critical for a *complete* twin:**
  - **Low** (~0.8 m) — floor, furniture bases.
  - **Mid** (~1.4 m) — eye level, the main pass.
  - **High / tilt up** (~1.8 m, angled upward) — **upper walls and CEILING.**
  > ⚠️ *Lesson learned:* our best capture still rendered a **black upper half** because
  > we only shot eye-level and down — the ceiling was never filmed, so there were no
  > splats there. **Deliberately tilt up and sweep the ceiling and wall-tops.**
- **Orbit key objects** (desk, sofa, reception) — walk a small arc around them.
- **Corners & doorways:** capture each from **two+ directions**.

## 4. Hard surfaces (mitigate SfM failure)
- **Mirrors / glossy floors:** never fill the frame with a reflection; shoot at oblique
  angles.
- **Windows / glass:** blinds partly closed or grazing angles; don't rely on glass for features.
- **Blank / textureless walls:** move slowly and keep a **corner or edge in frame** as a
  feature anchor; sweep adjacent textured areas.

## 5. Duration
- **~1.5–3 minutes per room** → ~300 sharp frames after sampling. (Below ~150 frames
  tends to fragment; see validation.)

## 6. File handling (don't lose your resolution!)
- **Transfer the ORIGINAL file** — **never send the video over WhatsApp/chat as a
  "video"** (it recompresses to ~480p). Use **USB cable, Google Drive (original
  quality), or WhatsApp "Document" mode**.
- **Format:** `.mp4` (H.264). **Name:** `data/raw/<space>_<date>_<take>.mp4`.

## 7. Post-capture validation (how to know it's good *before* training)
Run the pipeline's frames + COLMAP stages, then check:
- [ ] **Registered images ÷ extracted frames ≥ ~90%** in **one** model
      (`sparse/0`). Many sub-models or a low % = capture problem → recapture.
- [ ] **Sparse point count** is in the tens of thousands, not hundreds.
- [ ] Spot-check a few frames for motion blur; the pipeline auto-drops the blurriest 3%.

## 8. Empirical validation (this SOP works — measured)
Same room, two captures through the identical pipeline:

| Capture | Result |
|---|---|
| WhatsApp-shared, 848×478, fast motion | **132 / 225** frames registered, **3 fragmented models**, 4.4k points — patchy, unrecognizable |
| **This SOP:** 4K, 3 min, slow, looped | **351 / 351** frames registered, **1 clean model**, **111k points** — complete, recognizable room |

The only change was following the SOP. Resolution + coverage + overlap did it.

---

## Metric scale (for Round 2)
COLMAP is accurate only *up to scale*. The ArUco markers from §1 fix **origin,
orientation, and metric scale** when detected in the frames — the reproducible way to
get real metres for obstacle-aware pathfinding. A ruler/A4 sheet in frame is a weaker
fallback.
