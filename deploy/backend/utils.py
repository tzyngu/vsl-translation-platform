import re
import uuid
from pathlib import Path

def new_id() -> str:
    return str(uuid.uuid4())


def serialize(document):
    if document is None:
        return None
    if isinstance(document, list):
        return [serialize(item) for item in document]
    if isinstance(document, dict):
        return {key: serialize(value) for key, value in document.items()}
    if isinstance(document, uuid.UUID):
        return str(document)
    if hasattr(document, "isoformat"):
        return document.isoformat()
    return document


def safe_filename(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", Path(value).name).strip("._")
    return cleaned or "upload.bin"
