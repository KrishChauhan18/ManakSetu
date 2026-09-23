import os
import re
import uuid
import shutil
from typing import Optional
from abc import ABC, abstractmethod
from app.core.config import settings

STORAGE_ROOT = os.path.abspath(getattr(settings, "STORAGE_DIR", os.path.join(os.getcwd(), "storage")))

# Canonical subdirectories
SUBDIRS = ["uploads", "processed", "annotated", "reports", "temp"]
for sub in SUBDIRS:
    os.makedirs(os.path.join(STORAGE_ROOT, sub), exist_ok=True)
# Backward-compatibility folder for older scans
os.makedirs(os.path.join(STORAGE_ROOT, "images"), exist_ok=True)


class BaseStorageBackend(ABC):
    @abstractmethod
    def save_upload(self, file_bytes: bytes, original_filename: str, category: str = "uploads") -> str:
        pass

    @abstractmethod
    def save_bytes(self, data: bytes, relative_key: str) -> str:
        pass

    @abstractmethod
    def resolve_path(self, relative_key: str) -> str:
        pass

    @abstractmethod
    def exists(self, relative_key: str) -> bool:
        pass

    @abstractmethod
    def delete(self, relative_key: str) -> bool:
        pass

    @abstractmethod
    def public_url(self, relative_key: str) -> str:
        pass


class LocalStorageBackend(BaseStorageBackend):
    def __init__(self, root_dir: str = STORAGE_ROOT):
        self.root_dir = os.path.abspath(root_dir)
        for sub in SUBDIRS:
            os.makedirs(os.path.join(self.root_dir, sub), exist_ok=True)

    def safe_filename(self, filename: str) -> str:
        """Sanitize filename to prevent directory traversal and illegal characters."""
        base = os.path.basename(filename)
        # Strip path traversal attempts and keep alphanumeric, dashes, dots, underscores
        clean = re.sub(r'[^a-zA-Z0-9_.-]', '_', base)
        return clean or f"file_{uuid.uuid4().hex[:8]}"

    def validate_path(self, relative_or_abs: str) -> str:
        """
        Validate path and strictly prevent path traversal attacks.
        Returns normalized absolute path inside self.root_dir.

        Handles legacy paths that were stored with a leading './storage\\' or 'storage/'
        prefix from an older version of the code (e.g., './storage\\images\\uuid.jpg').
        """
        if not relative_or_abs:
            raise ValueError("Path cannot be empty.")

        # Normalize slashes for consistent handling across OS
        norm = relative_or_abs.replace("\\", "/")

        # Strip legacy leading './' to make detection easier
        if norm.startswith("./"):
            norm = norm[2:]

        # Strip legacy 'storage/' prefix that was embedded in old DB records.
        # The STORAGE_ROOT itself is called 'storage', so paths like 'storage/images/...'
        # should resolve to 'images/...' relative to root_dir.
        storage_folder = os.path.basename(self.root_dir)  # e.g. 'storage'
        prefix_slash = storage_folder + "/"
        if norm.lower().startswith(prefix_slash.lower()):
            norm = norm[len(prefix_slash):]

        # If absolute, normalize it; if relative, join with root
        if os.path.isabs(norm):
            target = os.path.abspath(norm)
        else:
            norm_rel = norm.lstrip("/")
            target = os.path.abspath(os.path.join(self.root_dir, norm_rel))

        # Enforce target must be inside root_dir
        if not target.startswith(self.root_dir):
            raise PermissionError(f"Access denied: Path traversal detected for '{relative_or_abs}'.")
        return target

    def save_upload(self, file_bytes: bytes, original_filename: str, category: str = "uploads") -> str:
        """
        Saves uploaded file into safe storage subdirectory.
        Returns normalized relative storage key (e.g. 'uploads/uuid.jpg').
        """
        cat_dir = category if category in SUBDIRS else "uploads"
        target_dir = os.path.join(self.root_dir, cat_dir)
        os.makedirs(target_dir, exist_ok=True)

        ext = os.path.splitext(original_filename)[1].lower() or ".jpg"
        clean_ext = re.sub(r'[^a-z0-9.]', '', ext)
        if clean_ext not in [".jpg", ".jpeg", ".png", ".webp", ".pdf"]:
            clean_ext = ".jpg"

        unique_filename = f"{uuid.uuid4().hex}{clean_ext}"
        abs_path = os.path.join(target_dir, unique_filename)

        with open(abs_path, "wb") as f:
            f.write(file_bytes)

        # Return relative storage key using forward slashes
        return f"{cat_dir}/{unique_filename}"

    def save_bytes(self, data: bytes, relative_key: str) -> str:
        """Saves arbitrary bytes to a relative key path within storage."""
        abs_path = self.validate_path(relative_key)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, "wb") as f:
            f.write(data)
        return relative_key.replace("\\", "/")

    def resolve_path(self, relative_or_abs: str) -> str:
        """Resolves relative storage key or valid absolute path to canonical local path."""
        return self.validate_path(relative_or_abs)

    def exists(self, relative_key: str) -> bool:
        try:
            path = self.resolve_path(relative_key)
            return os.path.exists(path) and os.path.isfile(path)
        except Exception:
            return False

    def delete(self, relative_key: str) -> bool:
        try:
            path = self.resolve_path(relative_key)
            if os.path.exists(path):
                os.remove(path)
                return True
        except Exception:
            pass
        return False

    def public_url(self, relative_key: str) -> str:
        norm_key = relative_key.replace("\\", "/").lstrip("/")
        return f"/storage/{norm_key}"

    # Backwards compatibility methods
    def save_image(self, file_bytes: bytes, filename: str) -> str:
        return self.save_upload(file_bytes, filename, category="uploads")

    def get_image_path(self, filename: str) -> str:
        return self.resolve_path(os.path.join("uploads", filename))

    def get_report_path(self, filename: str) -> str:
        return self.resolve_path(os.path.join("reports", filename))

    def save_report_pdf(self, pdf_bytes: bytes, scan_id: int) -> str:
        rel_key = f"reports/report_scan_{scan_id}.pdf"
        self.save_bytes(pdf_bytes, rel_key)
        return rel_key


class S3StorageBackend(BaseStorageBackend):
    """
    S3 / Cloud Object Storage interface prepared for future cloud deployment.
    """
    def __init__(self, bucket_name: Optional[str] = None, region: str = "ap-south-1"):
        self.bucket_name = bucket_name or os.getenv("S3_BUCKET_NAME", "complyerg-storage")
        self.region = region

    def save_upload(self, file_bytes: bytes, original_filename: str, category: str = "uploads") -> str:
        raise NotImplementedError("S3 storage backend is planned for cloud deployment.")

    def save_bytes(self, data: bytes, relative_key: str) -> str:
        raise NotImplementedError("S3 storage backend is planned for cloud deployment.")

    def resolve_path(self, relative_key: str) -> str:
        raise NotImplementedError("Direct filesystem path resolution not applicable for S3 storage.")

    def exists(self, relative_key: str) -> bool:
        return False

    def delete(self, relative_key: str) -> bool:
        return False

    def public_url(self, relative_key: str) -> str:
        return f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{relative_key}"


# Export singleton instance and convenience helpers
storage_backend = LocalStorageBackend()

def save_upload(file_bytes: bytes, original_filename: str) -> str:
    return storage_backend.save_upload(file_bytes, original_filename)

def get_file_path(relative_path: str) -> str:
    return storage_backend.resolve_path(relative_path)
