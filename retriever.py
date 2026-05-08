import re


def score_chunk(
    query: str,
    chunk: str
):

    query_words = re.findall(
        r"\w+",
        query.lower()
    )

    chunk_lower = chunk.lower()

    score = 0

    for word in query_words:

        if len(word) < 3:
            continue

        score += chunk_lower.count(word)

    return score


def retrieve_relevant_chunks(
    query: str,
    chunks: list[str],
    top_k: int = 3
):

    scored = []

    for chunk in chunks:

        score = score_chunk(
            query,
            chunk
        )

        scored.append(
            (score, chunk)
        )

    scored.sort(
        key=lambda x: x[0],
        reverse=True
    )

    results = []

    for score, chunk in scored[:top_k]:

        if score > 0:
            results.append(chunk)

    return results