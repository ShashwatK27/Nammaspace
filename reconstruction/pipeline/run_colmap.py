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
        vocab = cfg.get("vocab_tree_path",
                        "reconstruction/assets/vocab_tree_flickr100K_words32K.bin")
        if cfg.get("loop_detection", True) and os.path.exists(vocab):
            match_cmd += ["--SequentialMatching.loop_detection", "1",
                          "--SequentialMatching.vocab_tree_path", vocab]
        elif cfg.get("loop_detection", True):
            print(f"[run_colmap] loop_detection requested but vocab tree not found at "
                  f"{vocab}; continuing without it (may fragment).", file=sys.stderr)

    steps = [
        [colmap, "feature_extractor", "--database_path", db, "--image_path", frames,
         "--ImageReader.camera_model", model, "--ImageReader.single_camera", single,
         "--FeatureExtraction.use_gpu", gpu],
        match_cmd,
        [colmap, "mapper", "--database_path", db, "--image_path", frames,
         "--output_path", sparse],
    ]

    if run:
        os.makedirs(sparse, exist_ok=True)
    for cmd in steps:
        print("[run_colmap]", " ".join(cmd))
        if not run:
            continue
        rc = subprocess.call(cmd)
        if rc != 0:
            print(f"[run_colmap] step failed: {cmd[1]}", file=sys.stderr)
            return rc

    if not run:
        print("[run_colmap] dry-run (pass --run to execute)")
        return 0

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
