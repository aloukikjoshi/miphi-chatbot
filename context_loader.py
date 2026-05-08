from pathlib import Path

CONTEXT_FILE = Path("data/company_context.txt")


def load_context() -> str:
    if not CONTEXT_FILE.exists():
        return ""

    return CONTEXT_FILE.read_text(
        encoding="utf-8"
    ).strip()