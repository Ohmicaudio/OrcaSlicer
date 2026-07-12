#!/usr/bin/env python3
"""Read-only streaming inventory for Orca/Bambu-style 3MF projects."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, BinaryIO


ROOT_MODEL = "3D/3dmodel.model"
MODEL_SETTINGS = "Metadata/model_settings.config"
PROJECT_SETTINGS = "Metadata/project_settings.config"
REQUIRED_MEMBERS = {ROOT_MODEL, MODEL_SETTINGS, PROJECT_SETTINGS}
SCHEMA_VERSION = "0.1"


class ObservationError(ValueError):
    """Raised when a 3MF cannot produce a trustworthy observation report."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def observe_3mf(source: Path) -> dict[str, Any]:
    source = Path(source)
    try:
        with zipfile.ZipFile(source, "r") as archive:
            infos = archive.infolist()
            names = {item.filename for item in infos}
            missing = sorted(REQUIRED_MEMBERS - names)
            if missing:
                raise ObservationError(
                    "missing required member(s): " + ", ".join(missing)
                )
            return {
                "schema_version": SCHEMA_VERSION,
                "source": {
                    "file_name": source.name,
                    "sha256": sha256_file(source),
                    "compressed_size": source.stat().st_size,
                    "member_count": len(infos),
                    "uncompressed_member_bytes": sum(item.file_size for item in infos),
                    "required_members": sorted(REQUIRED_MEMBERS),
                },
                "project": {},
                "physical_tools": {
                    "nozzle_diameters": [],
                    "source_member": PROJECT_SETTINGS,
                },
                "materials": [],
                "plates": [],
                "objects": [],
                "warnings": [],
            }
    except (OSError, zipfile.BadZipFile) as exc:
        raise ObservationError(f"unreadable 3MF archive: {exc}") from exc
