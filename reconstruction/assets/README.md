# Reconstruction assets

## Vocabulary tree (COLMAP loop closure)

`run_colmap.py` enables vocabulary-tree **loop detection** on the sequential
matcher so revisited areas and adjacent rooms reconnect into a single model
instead of fragmenting.

**No manual download is needed.** COLMAP 3.12+ (faiss-based) **auto-downloads and
caches** a compatible vocab tree the first time loop detection runs, as long as
no explicit tree path is given. That's why `colmap.vocab_tree_path` is empty in
`config/pipeline.json`.

Only set `colmap.vocab_tree_path` if you have a **faiss-format** tree you want to
use offline. Legacy FLANN trees (e.g. the old `vocab_tree_flickr100K_words32K.bin`
from demuc.de) are **not** compatible with faiss builds and will error — don't
use them. `*.bin` here is gitignored.
