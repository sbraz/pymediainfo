#!/usr/bin/env python3

# ruff: noqa: T201
"""Update the version of the bundled MediaInfo library and its hashes in pyproject.toml."""

from __future__ import annotations

import argparse
from pathlib import Path
from tempfile import TemporaryDirectory

import requests
import tomlkit
from download_library import ALLOWED_ARCHS, PYPROJECT_FILE, TIMEOUT, Downloader

#: GitHub API URL of the latest MediaInfoLib release
LATEST_RELEASE_URL = "https://api.github.com/repos/MediaArea/MediaInfoLib/releases/latest"


def get_latest_version() -> str:
    """Get the version of the latest MediaInfoLib release."""
    response = requests.get(LATEST_RELEASE_URL, timeout=TIMEOUT)
    response.raise_for_status()
    # Tags are named after the version, e.g. v26.10
    return str(response.json()["tag_name"]).removeprefix("v")


def get_hashes(version: str) -> dict[str, str]:
    """Download the files of a MediaInfo version and get their BLAKE2b hashes."""
    hashes: dict[str, str] = {}
    for platform, archs in ALLOWED_ARCHS.items():
        for arch in archs:
            downloader = Downloader(platform=platform, arch=arch, version=version)
            suffix = downloader.get_compressed_file_suffix()
            # The same macOS file is used for x86_64 and arm64
            if suffix in hashes:
                continue
            url = downloader.get_url()
            print(f"Downloading {url}")
            with TemporaryDirectory() as tmp_dir:
                outpath = Path(tmp_dir) / downloader.get_compressed_file_name()
                hashes[suffix] = downloader.download_upstream(url, outpath)
    return hashes


def update_pyproject(version: str, new_hashes: dict[str, str]) -> None:
    """Write the version and hashes to pyproject.toml, keeping its formatting."""
    config = tomlkit.parse(PYPROJECT_FILE.read_text(encoding="utf-8"))
    bundled_library = config["tool"]["pymediainfo"]["bundled-library"]
    bundled_library["version"] = version
    # Change the existing table in place: replacing it would lose the comments
    # and blank lines that follow it
    pyproject_hashes = bundled_library["blake2b"]
    for suffix in set(pyproject_hashes) - new_hashes.keys():
        del pyproject_hashes[suffix]
    for suffix, blake2b_hash in sorted(new_hashes.items()):
        pyproject_hashes[suffix] = blake2b_hash
    PYPROJECT_FILE.write_text(tomlkit.dumps(config), encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "version",
        nargs="?",
        help="MediaInfo version to bundle (default: the latest release)",
    )
    args = parser.parse_args()

    version = args.version or get_latest_version()
    print(f"Using MediaInfo {version}")
    update_pyproject(version, get_hashes(version))
    print(f"Updated {PYPROJECT_FILE}")
