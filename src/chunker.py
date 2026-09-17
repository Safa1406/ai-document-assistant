def _find_chunk_end(text, start, chunk_size):
    target_end = min(start + chunk_size, len(text))

    if target_end >= len(text):
        return len(text)

    min_end = start + int(chunk_size * 0.6)

    separators = [
        "\n\n",
        "\n",
        ". ",
        "? ",
        "! ",
        "؟ ",
        "؛ ",
        "; ",
        "، ",
        ", ",
        " ",
    ]

    for separator in separators:
        position = text.rfind(
            separator,
            min_end,
            target_end,
        )

        if position != -1:
            return position + len(separator)

    return target_end


def _move_start_to_word_boundary(
    text,
    start,
    previous_start,
):
    if start <= 0:
        return 0

    minimum = max(
        previous_start + 1,
        start - 80,
    )

    candidate = start

    while (
        candidate > minimum
        and candidate > 0
        and not text[candidate - 1].isspace()
    ):
        candidate -= 1

    if candidate <= previous_start:
        return start

    return candidate


def create_chunks(
    pages,
    chunk_size=1000,
    overlap=200,
):
    if chunk_size <= 0:
        raise ValueError(
            "chunk_size must be greater than 0"
        )

    if overlap < 0 or overlap >= chunk_size:
        raise ValueError(
            "overlap must be >= 0 and smaller than chunk_size"
        )

    chunks = []

    for page in pages:
        text = page["text"].strip()

        if not text:
            continue

        start = 0
        chunk_number = 1

        while start < len(text):

            end = _find_chunk_end(
                text=text,
                start=start,
                chunk_size=chunk_size,
            )

            chunk_text = text[start:end].strip()

            if chunk_text:
                chunks.append(
                    {
                        "file_name": page["file_name"],
                        "page": page["page"],
                        "chunk_number": chunk_number,
                        "text": chunk_text,
                    }
                )

            if end >= len(text):
                break

            next_start = max(
                end - overlap,
                start + 1,
            )

            next_start = _move_start_to_word_boundary(
                text=text,
                start=next_start,
                previous_start=start,
            )

            start = next_start
            chunk_number += 1

    return chunks