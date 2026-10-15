import hashlib
from typing import BinaryIO

def compute_sha256_file(filepath: str, chunk_size: int = 65536) -> str:
    """Computes SHA-256 hash of a file on disk by reading in streaming chunks."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().lower()

def compute_sha256_bytes(data: bytes) -> str:
    """Computes SHA-256 hash of a bytes object."""
    return hashlib.sha256(data).hexdigest().lower()

# Compatibility alias for services importing calculate_sha256
calculate_sha256 = compute_sha256_file
