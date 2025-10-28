"""Quality estimation metrics for machine translation."""
from __future__ import annotations

import math
from collections import Counter
from typing import Iterable, List, Sequence


class MetricError(RuntimeError):
    """Raised when metric computation fails."""


def _extract_ngrams(tokens: Sequence[str], max_order: int) -> Counter:
    ngrams = Counter()
    for order in range(1, max_order + 1):
        for i in range(len(tokens) - order + 1):
            ngram = tuple(tokens[i : i + order])
            ngrams[ngram] += 1
    return ngrams


def compute_bleu(
    translations: Iterable[str],
    references: Iterable[str],
    *,
    max_order: int = 4,
    smooth: bool = True,
) -> float:
    """Compute a BLEU score between translations and references."""

    translations_list = list(translations)
    references_list = list(references)
    if len(translations_list) != len(references_list):
        raise MetricError("Translations and references must have the same length")
    if not translations_list:
        raise MetricError("At least one translation is required")

    matches_by_order = [0] * max_order
    possible_matches_by_order = [0] * max_order
    reference_length = 0
    translation_length = 0

    for translation, reference in zip(translations_list, references_list):
        translation_tokens = translation.split()
        reference_tokens = reference.split()
        translation_length += len(translation_tokens)
        reference_length += len(reference_tokens)

        ref_ngrams = _extract_ngrams(reference_tokens, max_order)
        trans_ngrams = _extract_ngrams(translation_tokens, max_order)
        overlap = ref_ngrams & trans_ngrams

        for ngram, count in overlap.items():
            matches_by_order[len(ngram) - 1] += count
        for order in range(1, max_order + 1):
            possible = len(translation_tokens) - order + 1
            if possible > 0:
                possible_matches_by_order[order - 1] += possible

    precisions: List[float] = []
    for order in range(max_order):
        if possible_matches_by_order[order] == 0:
            precisions.append(0.0)
        else:
            precision = matches_by_order[order] / possible_matches_by_order[order]
            if matches_by_order[order] == 0 and smooth:
                precision = 1.0 / (possible_matches_by_order[order] * 2)
            precisions.append(precision)

    if min(precisions) <= 0:
        geo_mean = 0.0
    else:
        geo_mean = math.exp(sum(math.log(p) for p in precisions) / max_order)

    ratio = translation_length / reference_length if reference_length > 0 else 0.0
    if ratio > 1.0:
        bp = 1.0
    elif ratio == 0:
        bp = 0.0
    else:
        bp = math.exp(1 - 1 / ratio)

    return bp * geo_mean


__all__ = ["compute_bleu", "MetricError"]
