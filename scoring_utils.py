#!/usr/bin/env python3
"""Shared deterministic text scoring helpers for Patent Miner."""

from __future__ import annotations

import math
import re
from collections import Counter
from typing import Dict, Iterable, List, Sequence

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "in",
    "into",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "to",
    "with",
}


def clamp(value: float, lower: float = 0.0, upper: float = 10.0) -> float:
    """Clamp a numeric value into a bounded range."""

    return max(lower, min(upper, value))


def normalize_text(text: str) -> str:
    """Normalize text for deterministic token matching."""

    text = (text or "").lower()
    return re.sub(r"[^a-z0-9\s]+", " ", text)


def tokenize_text(text: str) -> List[str]:
    """Tokenize text and drop short/common stopwords."""

    normalized = normalize_text(text)
    tokens = [tok for tok in normalized.split() if len(tok) > 1 and tok not in STOPWORDS]
    return tokens


def term_coverage(query_terms: Iterable[str], text_tokens: Sequence[str]) -> float:
    """Return the fraction of query terms present in the text token set."""

    query = {term for term in query_terms if term}
    if not query:
        return 0.0

    token_set = set(text_tokens)
    hits = sum(1 for term in query if term in token_set)
    return hits / float(len(query))


def build_idf(corpus_tokens: Sequence[Sequence[str]]) -> Dict[str, float]:
    """Build IDF values using smooth weighting."""

    if not corpus_tokens:
        return {}

    doc_count = len(corpus_tokens)
    document_frequency: Counter[str] = Counter()
    for tokens in corpus_tokens:
        document_frequency.update(set(tokens))

    return {
        token: math.log((1.0 + doc_count) / (1.0 + freq)) + 1.0
        for token, freq in document_frequency.items()
    }


def tfidf_vector(tokens: Sequence[str], idf: Dict[str, float]) -> Dict[str, float]:
    """Build sparse TF-IDF vector from token sequence and IDF map."""

    if not tokens:
        return {}

    counts: Counter[str] = Counter(tokens)
    size = float(len(tokens))
    vector: Dict[str, float] = {}
    for token, count in counts.items():
        tf = count / size
        vector[token] = tf * idf.get(token, 1.0)
    return vector


def cosine_similarity(vec_a: Dict[str, float], vec_b: Dict[str, float]) -> float:
    """Cosine similarity for sparse dict vectors."""

    if not vec_a or not vec_b:
        return 0.0

    intersection = set(vec_a).intersection(vec_b)
    dot = sum(vec_a[token] * vec_b[token] for token in intersection)

    norm_a = math.sqrt(sum(value * value for value in vec_a.values()))
    norm_b = math.sqrt(sum(value * value for value in vec_b.values()))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0

    return dot / (norm_a * norm_b)


def tfidf_cosine_similarity(query_text: str, doc_text: str, corpus_docs: Sequence[str]) -> float:
    """Compute cosine similarity using TF-IDF vectors built from corpus + query + doc."""

    query_tokens = tokenize_text(query_text)
    doc_tokens = tokenize_text(doc_text)

    corpus_tokens = [tokenize_text(doc) for doc in corpus_docs]
    corpus_tokens.extend([query_tokens, doc_tokens])

    idf = build_idf(corpus_tokens)
    query_vec = tfidf_vector(query_tokens, idf)
    doc_vec = tfidf_vector(doc_tokens, idf)

    return cosine_similarity(query_vec, doc_vec)
