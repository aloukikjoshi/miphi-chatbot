from pathlib import Path

CONTEXT_FILE = Path(
    "data/company_context.txt"
)


def load_context_chunks():

    if not CONTEXT_FILE.exists():
        return []

    raw_text = CONTEXT_FILE.read_text(
        encoding="utf-8"
    )

    chunks = []

    current_chunk = []

    current_length = 0

    max_chunk_size = 1200

    paragraphs = raw_text.split("\n\n")

    for para in paragraphs:

        para = para.strip()

        if not para:
            continue

        if (
            current_length + len(para)
            > max_chunk_size
        ):

            chunks.append(
                "\n\n".join(current_chunk)
            )

            current_chunk = []
            current_length = 0

        current_chunk.append(para)

        current_length += len(para)

    if current_chunk:
        chunks.append(
            "\n\n".join(current_chunk)
        )

    return chunks