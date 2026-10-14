import os
import re
import uuid
import shutil
from typing import BinaryIO, Tuple
from app.core.config import get_settings
from app.core.exceptions import StorageException
from app.utils.hashing import compute_sha256_file

settings = get_settings()

class StorageManager:
    """Manages file storage safely on local disk, ensuring path containment and atomic writes."""

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        clean = os.path.basename(filename.strip())
        name, ext = os.path.splitext(clean)
        safe_name = re.sub(r"[^a-zA-Z0-9_-]", "_", name)
        safe_ext = re.sub(r"[^a-zA-Z0-9.]", "", ext).lower()
        return f"{safe_name}{safe_ext}"

    @staticmethod
    def get_safe_path(base_dir: str, relative_path: str) -> str:
        """Validates that relative_path resolves strictly within base_dir, preventing path traversal."""
        full_base = os.path.abspath(base_dir)
        target = os.path.abspath(os.path.join(full_base, relative_path))
        if not target.startswith(full_base):
            raise StorageException(f"Path traversal detected: '{relative_path}' escapes storage root.")
        return target

    @classmethod
    def save_upload_stream(
        cls,
        file_obj: BinaryIO,
        original_filename: str,
        max_bytes: int = 500 * 1024 * 1024
    ) -> Tuple[str, str, int, str]:
        """
        Streams uploaded file directly to disk, computes SHA-256 simultaneously,
        and enforces maximum byte constraints.
        Returns: (saved_relative_path, safe_filename, total_bytes, sha256_hash)
        """
        import hashlib

        safe_name = cls.sanitize_filename(original_filename)
        unique_prefix = uuid.uuid4().hex[:12]
        stored_filename = f"{unique_prefix}_{safe_name}"
        destination = cls.get_safe_path(settings.uploads_path, stored_filename)

        temp_dest = f"{destination}.tmp_{uuid.uuid4().hex[:6]}"
        hasher = hashlib.sha256()
        total_bytes = 0

        try:
            with open(temp_dest, "wb") as out_f:
                while True:
                    chunk = file_obj.read(1024 * 1024)  # 1MB chunk
                    if not chunk:
                        break
                    total_bytes += len(chunk)
                    if total_bytes > max_bytes:
                        raise StorageException(f"Uploaded file exceeds maximum allowed limit of {max_bytes} bytes.")
                    hasher.update(chunk)
                    out_f.write(chunk)

            if total_bytes == 0:
                raise StorageException("Uploaded file is empty (0 bytes).")

            # Atomic rename
            os.replace(temp_dest, destination)
            sha256_hash = hasher.hexdigest().lower()
            rel_path = os.path.relpath(destination, settings.BASE_DIR).replace("\\", "/")
            return rel_path, safe_name, total_bytes, sha256_hash
        except Exception:
            if os.path.exists(temp_dest):
                os.remove(temp_dest)
            if os.path.exists(destination):
                os.remove(destination)
            raise

    @classmethod
    def delete_file(cls, file_path: str) -> bool:
        """Safely removes a file from disk if it exists and resides within storage boundaries."""
        abs_path = os.path.abspath(os.path.join(settings.BASE_DIR, file_path)) if not os.path.isabs(file_path) else file_path
        if not abs_path.startswith(os.path.abspath(settings.BASE_DIR)):
            raise StorageException("Cannot delete files outside Kestral storage root.")
        if os.path.exists(abs_path) and os.path.isfile(abs_path):
            os.remove(abs_path)
            return True
        return False
