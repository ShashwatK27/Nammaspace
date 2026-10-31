# Reconstruction assets

## Vocabulary tree (for COLMAP loop closure)

`run_colmap.py` enables vocabulary-tree **loop detection** on the sequential
matcher so that revisited areas and adjacent rooms reconnect into a single model
instead of fragmenting. It needs a vocab tree, which is not committed (≈15 MB).

Download it once:

```bash
curl -L -o reconstruction/assets/vocab_tree_flickr100K_words32K.bin \
  https://demuc.de/colmap/vocab_tree_flickr100K_words32K.bin
```

Path is configurable via `colmap.vocab_tree_path` in `config/pipeline.json`
(or the `COLMAP_VOCAB_TREE` env). If the file is missing, matching falls back
to sequential-only (no loop closure) with a warning.
