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
Two things matter more than everything else combined: **sharp frames** and **parallax**.
A blurry frame doesn't just blur one spot — the blur spreads through the whole
reconstruction as haze and floaters, and it can't be recovered later. Parallax (the way
near and far objects shift as you *move*) is what gives depth; panning on the spot gives
none and the scene collapses into mush.

So, for every surface you want in the twin:
1. **Sharp frames above all** — fast shutter, no motion blur. Fewer sharp frames beat
   many blurry ones.
2. **Parallax — WALK, never pan.** Move your feet; don't rotate on the spot.
3. **Multiple viewpoints** of each surface (≥3 angles) at **70–80% overlap** between
   consecutive frames (70% is the floor, 80% is better — this is what lets SfM solve poses).
4. **Texture** — featureless walls, mirrors and glass are the enemies.

Everything below serves those four.

---

## 1. Pre-capture checklist (2 minutes, do every time)
- [ ] **Resolution 1080p or 4K.** Phone's native camera app. *(A chat-app-shared clip
      gets silently recompressed to ~480p and reconstructs poorly — see §6 for transfer.)*
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
| Resolution | **4K** (1080p only if you must) | detail = fidelity; 4K is a clear step up |
| Frame rate | **30 fps** | we sample 2–4 fps later; 60 just wastes storage |
| **Shutter speed** | **≥ 1/500 s, locked** | **the #1 rule — stops motion blur.** Sacrifice ISO (sensor noise is fine; blur is fatal) |
| Bitrate / codec | **Max bitrate, H.265** | keep detail; ProRes is overkill (~10 GB/min) |
| Exposure/Focus | **Locked** | no flicker / refocus blur |
| Stabilization | On (standard) | avoid heavy "action/warp" modes |
| Orientation | **Landscape**, kept consistent | don't rotate phone mid-capture |

> The stock camera hides shutter speed and keeps changing it. For control, use a
> **manual video app** that lets you **lock shutter ≥ 1/500 s** (Android: *mcpro24fps*,
> *MotionCam*, or the phone's **Pro video** mode; iOS: *Blackmagic Camera*, free).
> **Clean the lens first.** Use the **main** rear lens — avoid the ultra-wide (0.5×): its
> distortion is harder for SfM and the rasterised splat.

## 3. Capture procedure (the walk)
- **WALK, don't pan.** Move your feet through the space — never stand in one spot and
  rotate. Panning gives no parallax and the reconstruction collapses. *Zoom with your feet.*
- **Speed:** slow, steady walk. **Smooth turns only** — never whip the phone around
  (abrupt motion = blur). Hold the phone **landscape, angled slightly** (not dead-straight)
  — it generates parallax more efficiently.
- **Pattern:** a gradual **spiral** gives the smoothest coverage. Walk slowly **along each
  wall**, **cross through the centre**, orbit furniture, then **loop back the other way**
  (loop closure reconnects the model — our COLMAP now uses it, so one walkthrough can
  cover several rooms as a single scene).
- **Cover every surface from ≥3 angles**, with **60–80% overlap** between views.
- **Three heights — this is critical for a *complete* twin:**
  - **Low** (~0.8 m) — floor, furniture bases.
  - **Mid** (~1.4 m) — eye level, the main pass.
  - **High / tilt up** (~1.8 m, angled upward) — **upper walls and CEILING.**
  > ⚠️ *Why this matters:* if you only shoot eye-level and down, the ceiling is never
  > filmed, so it has no splats and renders as a gap. **Deliberately tilt up and sweep
  > the ceiling and wall-tops.**
- **Orbit key objects** (desk, sofa, reception) — walk a small arc around them. When a full
  circle is blocked by a wall or furniture, use a **concave half-shell arc**: move along a
  curve while keeping the camera pointed at the object; shoot the area with **several arcs at
  different heights**. **Avoid convex paths** (camera pointing *outward* from the arc) — they
  make 70–80% overlap much harder to hold and often break the solve.
- **Corners & doorways:** capture each from **two+ directions**. Through a doorway,
  slow almost to a stop and sweep so **many frames see *both* rooms at once** — that
  overlap is what lets loop closure stitch the rooms into one model.
- **Shoot a bit *beyond* the area you'll show.** If you capture only exactly what you want
  viewers to see, the edges fall apart the moment they move past your path.

## 4. Hard surfaces (mitigate SfM failure)
- **Mirrors / glossy floors:** never fill the frame with a reflection; shoot at oblique
  angles. *Flat* mirrors can actually reconstruct cleanly (the reflection behaves as a
  consistent "mirror world") as long as two mirrors' reflections don't overlap; **curved
  reflective surfaces fail** — expect to clean those by hand. A **polarizing filter** cuts
  glare if your rig takes one.
- **Windows / glass:** blinds partly closed or grazing angles; don't rely on glass for features.
- **Blank / textureless walls & ceilings:** these are the hardest case — with no features to
  match they reconstruct as blurry "clouds" or holes. Move slowly, keep a **corner or edge
  in frame** as a feature anchor, shoot them from **many angles**, and sweep adjacent
  textured areas. Plan on some **manual cleanup** of walls/ceilings in editing — even
  professional whole-house captures accept this.

## 5. Duration & frame count
- **~1.5–3 minutes per room** → ~300 sharp frames after sampling. (Below ~150 frames
  tends to fragment; see validation.)
- **Target frames by scene size** (industry rule of thumb): a single **room ≈ 300–900**
  frames; a **multi-room / whole-floor walkthrough ≈ 1000–2000**. More coverage = denser
  twin — *"when in doubt, shoot more."*
- **Ceiling on one pass:** SfM slows sharply past **~5000 images** and can run out of
  memory. A **whole apartment/multiple floors is split into sections** and reconstructed
  separately, then recombined (recombining is genuinely hard — keep generous **overlap at
  the seams/doorways** so sections share enough views to align).
- **From video:** sample **every 2nd–5th frame** depending on walk speed, then **drop blurry
  frames** (our pipeline auto-drops the blurriest ~3%; the *Sharp Frames* tool —
  `sharp-frames.reflct.app` — does the same if selecting stills by hand).

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
| 4K multi-room walkthrough, **sequential-only** matching | 620 / 659 registered but **6 fragmented models** — doorways broke the chain |
| Same walkthrough, **+ vocab-tree loop closure** | **579 / 667 in ONE model** — the whole apartment reconnected as a single scene |

The only change was following the SOP (resolution + coverage + overlap), plus enabling
**loop closure** in COLMAP so multi-room walkthroughs stay one connected model.

---

## 9. External references (organizer-shared)
This SOP is corroborated by the two capture guides the organizers circulated, plus the
pipeline resources from Round 1. Our own measured results (§8) agree with all of them.
- **PlayCanvas — *Taking Photos for Gaussian Splatting***
  (`developer.playcanvas.com/user-manual/gaussian-splatting/creating/taking-photos/`):
  shutter **≥ 1/125 s** handheld, **ISO as low as possible**, **f/8–f/11** (deep depth of
  field — everything in focus), manual focus/exposure **locked** across the whole session,
  **4K / 60 fps+** video at max bitrate, **70–80% overlap**, **15–30°** between viewpoints,
  multiple elevations; overcast/diffuse light; avoid motion blur, reflective surfaces and
  moving objects.
- **Magnopus — *Lessons in Gaussian Splats from the Allee Willis House***
  (`magnopus.com/blog/lessons-in-gaussian-splats-from-the-allee-willis-house`): **overlap
  ≥ 70% (80% better) is the single biggest success factor**; move slowly, no motion blur
  (noise is tolerable — they reconstructed at **ISO 40,000**; blur is not); full
  circles/domes best, **concave half-shell arcs** where blocked, avoid convex paths;
  **flat mirrors OK, curved reflectors fail**; **white walls reconstruct as clouds** →
  many angles + manual cleanup; a **whole house is split into sections** and recombined;
  turn off heavy stabilization (IBIS) and use a **polarizer** for reflections.

> **Takeaway for NammaSpace:** every rule we already follow (sharp frames, walk-don't-pan,
> 70–80% overlap, loop closure, three heights, textureless-wall mitigation) is independently
> confirmed by both sources. The one thing neither solves is **seamless multi-room joining** —
> which is exactly why our COLMAP **loop closure** (one connected walkthrough) is a genuine
> advantage over split-and-recombine workflows.

---

## Metric scale (for Round 2)
COLMAP is accurate only *up to scale*. The ArUco markers from §1 fix **origin,
orientation, and metric scale** when detected in the frames — the reproducible way to
get real metres for obstacle-aware pathfinding. A ruler/A4 sheet in frame is a weaker
fallback.
