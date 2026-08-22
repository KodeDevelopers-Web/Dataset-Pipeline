"""
Tokenizer utilities.
Lazy loading.
The tokenizer is loaded only
when first used.
"""

from functools import lru_cache
from transformers import (
    AutoTokenizer
)
from config import (
    MODEL_NAME,
    MAX_TOKENS
)

@lru_cache(maxsize=1)
def get_tokenizer():
    return AutoTokenizer.from_pretrained(
        MODEL_NAME,
        trust_remote_code=False
    )

def count_tokens(text):
    tokenizer = get_tokenizer()
    return len(
        tokenizer.encode(
            text,
            add_special_tokens=False
        )
    )

def truncate(
    text,
    max_tokens=MAX_TOKENS
):
    tokenizer = get_tokenizer()
    ids = tokenizer.encode(
        text,
        add_special_tokens=False
    )

    ids = ids[:max_tokens]
    return tokenizer.decode(ids)

def sample_tokens(sample):
    return (
        count_tokens(
            sample["instruction"]
        )
        +
        count_tokens(
            sample["input"]
        )
        +
        count_tokens(
            sample["output"]
        )
    )

def within_limit(sample):
    return (
        sample_tokens(sample)
        <=
        MAX_TOKENS
    )