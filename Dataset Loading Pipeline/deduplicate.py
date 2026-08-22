"""
deduplicate.py
Near duplicate removal
using MinHashLSH.
"""

from datasketch import (
    MinHash,
    MinHashLSH
)
from config import (
    MINHASH_PERMUTATIONS,
    SIMILARITY_THRESHOLD
)
from merge import merge
from utils.logger import info

lsh = MinHashLSH(
    threshold=SIMILARITY_THRESHOLD,
    num_perm=MINHASH_PERMUTATIONS
)

def build_signature(text):
    signature = MinHash(
        num_perm=MINHASH_PERMUTATIONS
    )
    for token in text.split():
        signature.update(
            token.encode("utf8")
        )
    return signature

def deduplicate():
    processed = 0
    removed = 0
    kept = 0
    for sample in merge():
        processed += 1
        signature = build_signature(
            sample["output"]
        )

        duplicates = lsh.query(signature)
        if duplicates:
            removed += 1
            continue
        key = f"sample_{processed}"
        lsh.insert(
            key,
            signature
        )
        kept += 1
        if kept % 10000 == 0:
            info(
                f"Unique samples: "
                f"{kept:,}"
            )
        yield sample
    info("Deduplication complete")
    info(f"Processed : {processed:,}")
    info(f"Unique    : {kept:,}")
    info(f"Removed   : {removed:,}")


if __name__ == "__main__":
    iterator = deduplicate()
    for _ in range(10):
        print(next(iterator)["source"])