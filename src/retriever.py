import re
import unicodedata

import numpy as np


KEYWORD_WEIGHT = 0.35


STOP_WORDS = {
    # French
    "a",
    "au",
    "aux",
    "avec",
    "ce",
    "ces",
    "cet",
    "cette",
    "combien",
    "dans",
    "de",
    "des",
    "du",
    "elle",
    "en",
    "est",
    "et",
    "ete",
    "etre",
    "il",
    "ils",
    "la",
    "le",
    "les",
    "leur",
    "leurs",
    "ou",
    "par",
    "pour",
    "que",
    "quel",
    "quelle",
    "quelles",
    "quels",
    "qui",
    "sont",
    "sur",
    "un",
    "une",

    # English
    "a",
    "an",
    "and",
    "are",
    "for",
    "how",
    "in",
    "is",
    "of",
    "on",
    "or",
    "the",
    "to",
    "was",
    "were",
    "what",
    "when",
    "where",
    "which",
    "who",
    "why",
    "with",

    # Arabic
    "إلى",
    "الى",
    "التي",
    "الذي",
    "هذا",
    "هذه",
    "عن",
    "على",
    "في",
    "كيف",
    "كم",
    "لماذا",
    "ما",
    "ماذا",
    "من",
    "هل",
    "هو",
    "هي",
}


def _normalize_text(text):
    text = text.casefold()

    text = unicodedata.normalize(
        "NFKD",
        text,
    )

    text = "".join(
        character
        for character in text
        if not unicodedata.combining(character)
    )

    text = re.sub(
        r"[^\w]+",
        " ",
        text,
        flags=re.UNICODE,
    )

    return " ".join(
        text.split()
    )


def _extract_query_terms(query):
    normalized_query = _normalize_text(
        query
    )

    tokens = normalized_query.split()

    terms = []

    for token in tokens:
        if len(token) < 2:
            continue

        if token in STOP_WORDS:
            continue

        if token not in terms:
            terms.append(
                token
            )

    return terms


def _keyword_overlap_score(
    query_terms,
    text,
):
    if not query_terms:
        return 0.0

    normalized_text = _normalize_text(
        text
    )

    text_terms = set(
        normalized_text.split()
    )

    matches = sum(
        1
        for term in query_terms
        if term in text_terms
    )

    return matches / len(
        query_terms
    )


def retrieve_top_chunks(
    query,
    chunks,
    embeddings,
    model,
    top_k=3,
    min_score=0.35,
):
    query_embedding = model.encode(
        [query],
        convert_to_numpy=True,
    )[0]

    query_norm = np.linalg.norm(
        query_embedding
    )

    chunk_norms = np.linalg.norm(
        embeddings,
        axis=1,
    )

    scores = embeddings @ query_embedding

    scores = scores / (
        (chunk_norms * query_norm)
        + 1e-12
    )

    query_terms = _extract_query_terms(
        query
    )

    keyword_scores = np.zeros(
        len(chunks),
        dtype=float,
    )

    final_scores = scores.copy()

    for index, chunk in enumerate(
        chunks
    ):
        keyword_score = (
            _keyword_overlap_score(
                query_terms=query_terms,
                text=chunk["text"],
            )
        )

        keyword_scores[index] = (
            keyword_score
        )

        final_scores[index] += (
            KEYWORD_WEIGHT
            * keyword_score
        )

    acronyms = re.findall(
        r"\b[A-ZÀ-Ü]{2,}\b",
        query,
    )

    for index, chunk in enumerate(
        chunks
    ):
        text = chunk["text"]

        for acronym in acronyms:
            if re.search(
                rf"(?m)^\s*"
                rf"{re.escape(acronym)}"
                rf"\s*:",
                text,
            ):
                final_scores[index] += 0.40

    sorted_indices = np.argsort(
        final_scores
    )[::-1]

    results = []

    for index in sorted_indices:
        if (
            final_scores[index]
            < min_score
        ):
            continue

        chunk = chunks[index]

        results.append(
            {
                "score": float(
                    final_scores[index]
                ),
                "semantic_score": float(
                    scores[index]
                ),
                "keyword_score": float(
                    keyword_scores[index]
                ),
                "file_name": (
                    chunk["file_name"]
                ),
                "page": chunk["page"],
                "chunk_number": (
                    chunk["chunk_number"]
                ),
                "text": chunk["text"],
            }
        )

        if len(results) == top_k:
            break

    return results