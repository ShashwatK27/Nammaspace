"""Stage 2 — COLMAP Structure-from-Motion: frames -> camera poses + sparse cloud.

    python run_colmap.py --frames data/processed/scene-001/frames \\
        --out data/processed/scene-001/colmap

Sequential matcher (video frames are ordered). Emits a TXT model at
<out>/sparse/0/{cameras,images,points3D}.txt for build_scene.py.
Requires COLMAP on PATH. Use --run to execute (default prints the plan).
"""
from __future__ import annotations

import argparse
import glob
import os
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tools import load_config, resolve_tool  # noqa: E402


def _promote_largest_model(sparse: str) -> None:
    """COLMAP numbers sub-models in creation order, not size, so the biggest
    reconstruction is often sparse/1, not sparse/0. Downstream (train/build_scene)
    only reads sparse/0, so move the model with the most registered images there."""
    models = [d for d in glob.glob(os.path.join(sparse, "*"))
              if os.path.isfile(os.path.join(d, "images.bin"))
              or os.path.isfile(os.path.join(d, "images.txt"))]
    if len(models) <= 1:
        return

    def _nimages(d):
        for name in ("images.bin", "images.txt"):
            p = os.path.join(d, name)
            if os.path.isfile(p):
                return os.path.getsize(p)
        return 0

    largest = max(models, key=_nimages)
    if os.path.basename(largest) == "0":
        return
    zero = os.path.join(sparse, "0")
    stash = os.path.join(sparse, "_was0")
    if os.path.isdir(zero):
        shutil.rmtree(stash, ignore_errors=True)
        os.rename(zero, stash)
    os.rename(largest, zero)
    print(f"[run_colmap] promoted {os.path.basename(largest)} -> sparse/0 "
          f"(largest of {len(models)} models)")


def run_colmap(frames: str, out: str, full_cfg: dict, run: bool) -> int:
    cfg = full_cfg.get("colmap", {})
    colmap = resolve_tool("colmap", full_cfg, "COLMAP_BIN")
    db = os.path.join(out, "database.db")
    sparse = os.path.join(out, "sparse")
    gpu = "1" if cfg.get("use_gpu", True) else "0"
    model = cfg.get("camera_model", "OPENCV")
    single = "1" if cfg.get("single_camera", True) else "0"
    matcher_name = cfg.get("matcher", "sequential")
    matcher = matcher_name + "_matcher"

    match_cmd = [colmap, matcher, "--database_path", db, "--FeatureMatching.use_gpu", gpu]
    # Sequential video frames: widen the overlap window and add vocabulary-tree
    # LOOP CLOSURE so revisited areas / adjacent rooms reconnect instead of
    # fragmenting into separate models (the #1 failure on multi-room walkthroughs).
    if matcher_name == "sequential":
        match_cmd += ["--SequentialMatching.overlap", str(cfg.get("overlap", 20)),
                      "--SequentialMatching.quadratic_overlap", "1"]
        if cfg.get("loop_detection", True):
            match_cmd += ["--SequentialMatching.loop_detection", "1"]
            # COLMAP 3.12+ (faiss) auto-downloads and caches a compatible vocab
            # tree when none is given. Only pass an explicit path if the user
            # configured a faiss-format tree; a legacy FLANN tree will error.
            vocab = cfg.get("vocab_tree_path", "")
            if vocab and os.path.exists(vocab):
                match_cmd += ["--SequentialMatching.vocab_tree_path", vocab]

    extract_cmd = [colmap, "feature_extractor", "--database_path", db, "--image_path", frames,
                   "--ImageReader.camera_model", model, "--ImageReader.single_camera", single,
                   "--FeatureExtraction.use_gpu", gpu]
    mapper_cmd = [colmap, "mapper", "--database_path", db, "--image_path", frames,
                  "--output_path", sparse]

    print("[run_colmap]", " ".join(extract_cmd))
    print("[run_colmap]", " ".join(match_cmd))
    print("[run_colmap]", " ".join(mapper_cmd))
    if not run:
        print("[run_colmap] dry-run (pass --run to execute)")
        return 0

    os.makedirs(sparse, exist_ok=True)
    if subprocess.call(extract_cmd) != 0:
        print("[run_colmap] step failed: feature_extractor", file=sys.stderr)
        return 1

    if subprocess.call(match_cmd) != 0:
        # Loop closure needs a faiss vocab tree; if it's missing/legacy/incompatible
        # the matcher aborts. Fall back to plain sequential matching so a vocab-tree
        # problem degrades connectivity instead of killing the whole pipeline.
        if "--SequentialMatching.loop_detection" in match_cmd:
            print("[run_colmap] matcher failed with loop closure; retrying "
                  "sequential-only (no vocab tree). Expect more fragmentation.",
                  file=sys.stderr)
            i = match_cmd.index("--SequentialMatching.loop_detection")
            fallback = [a for j, a in enumerate(match_cmd)
                        if j not in (i, i + 1)]
            if "--SequentialMatching.vocab_tree_path" in fallback:
                k = fallback.index("--SequentialMatching.vocab_tree_path")
                fallback = [a for j, a in enumerate(fallback) if j not in (k, k + 1)]
            if subprocess.call(fallback) != 0:
                print("[run_colmap] step failed: sequential_matcher", file=sys.stderr)
                return 1
        else:
            print("[run_colmap] step failed: sequential_matcher", file=sys.stderr)
            return 1

    if subprocess.call(mapper_cmd) != 0:
        print("[run_colmap] step failed: mapper", file=sys.stderr)
        return 1

    _promote_largest_model(sparse)
    rc = subprocess.call([colmap, "model_converter",
                          "--input_path", os.path.join(sparse, "0"),
                          "--output_path", os.path.join(sparse, "0"),
                          "--output_type", "TXT"])
    if rc != 0:
        print("[run_colmap] step failed: model_converter", file=sys.stderr)
        return rc
    print(f"[run_colmap] TXT model at {os.path.join(sparse, '0')}")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--frames", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--config", default="reconstruction/config/pipeline.json")
    ap.add_argument("--run", action="store_true", help="execute (default: dry-run)")
    args = ap.parse_args(argv)
    return run_colmap(args.frames, args.out, load_config(args.config), args.run)


if __name__ == "__main__":
    raise SystemExit(main())
