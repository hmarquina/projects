"""Release package reproducible: zip determinista + manifest con hashes."""

import hashlib
import io
import json
import zipfile
from typing import Any

_FIXED_TIME = (1980, 1, 1, 0, 0, 0)


def build_package(files: dict[str, str], manifest: dict[str, Any]) -> bytes:
    payload = {**files, "MANIFEST.json": json.dumps(manifest, indent=2, sort_keys=True) + "\n"}
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(payload):
            info = zipfile.ZipInfo(path, date_time=_FIXED_TIME)
            info.external_attr = 0o644 << 16
            zf.writestr(info, payload[path])
    return buf.getvalue()


def package_hash(package: bytes) -> str:
    return hashlib.sha256(package).hexdigest()
