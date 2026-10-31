#!/usr/bin/env python3

# ruff: noqa: T201
"""Download binary library files from <https://mediaarea.net/en/MediaInfo/Download/>."""

from __future__ import annotations

import hashlib
import os
import shutil
import sys
import tarfile
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING, Any
from zipfile import ZipFile

import requests
import tomlkit

if TYPE_CHECKING:
    from typing import Literal, TypeAlias

    Platform: TypeAlias = Literal["linux", "darwin", "win32"]
    Arch: TypeAlias = Literal["x86_64", "arm64", "i386"]


#: Base URL for downloading MediaInfo library
BASE_URL: str = "https://mediaarea.net/download/binary/libmediainfo0"

#: Timeout of the download requests, in seconds
TIMEOUT: int = 20

#: pyproject.toml, which contains the version and hashes of the bundled library
PYPROJECT_FILE: Path = Path(__file__).resolve().parent.parent / "pyproject.toml"

#: Architectures for which MediaArea provides a library, for each platform
ALLOWED_ARCHS: dict[Platform, tuple[Arch, ...]] = {
    "linux": ("x86_64", "arm64"),
    "darwin": ("x86_64", "arm64"),
    "win32": ("x86_64", "arm64", "i386"),
}


def read_bundled_library_config() -> tuple[str, dict[str, str]]:
    """Get the version of the bundled library and the hashes of its files from pyproject.toml."""
    config = tomlkit.parse(PYPROJECT_FILE.read_text(encoding="utf-8")).unwrap()
    bundled_library = config["tool"]["pymediainfo"]["bundled-library"]
    return bundled_library["version"], bundled_library["blake2b"]


def get_file_blake2b(file_path: os.PathLike[str] | str, chunksize: int = 1 << 20) -> str:
    """Get the BLAKE2b hash of a file."""
    blake2b = hashlib.blake2b()
    with Path(file_path).open("rb") as f:
        while chunk := f.read(chunksize):
            blake2b.update(chunk)
    return blake2b.hexdigest()


@dataclass
class Downloader:
    """Downloader for the MediaInfo library files."""

    platform: Platform
    arch: Arch
    version: str

    def __post_init__(self) -> None:
        """Check that the combination of platform and arch is allowed."""
        allowed_arch = ALLOWED_ARCHS.get(self.platform)
        if allowed_arch is None:
            msg = f"platform not recognized: {self.platform}"
            raise ValueError(msg)

        # Check the platform and arch is a valid combination
        if self.arch not in allowed_arch:
            msg = (
                f"arch {self.arch} is not allowed for platform {self.platform}; "
                f"must be one of {allowed_arch}"
            )
            raise ValueError(msg)

    def get_compressed_file_suffix(self) -> str:
        """Get the end of the compressed file name, which doesn't depend on the version."""
        if self.platform == "linux":
            suffix = f"Lambda_{self.arch}.zip"
        elif self.platform == "darwin":
            suffix = "Mac_x86_64+arm64.tar.bz2"
        elif self.platform == "win32":
            win_arch = {"x86_64": "x64", "arm64": "ARM64"}.get(self.arch, self.arch)
            suffix = f"Windows_{win_arch}_WithoutInstaller.zip"
        else:
            msg = f"platform not recognized: {self.platform}"
            raise ValueError(msg)
        return suffix

    def get_compressed_file_name(self) -> str:
        """Get the compressed file name."""
        return f"MediaInfo_DLL_{self.version}_{self.get_compressed_file_suffix()}"

    def get_url(self) -> str:
        """Get the URL to download the MediaInfo library."""
        compressed_file = self.get_compressed_file_name()
        return f"{BASE_URL}/{self.version}/{compressed_file}"

    def download_upstream(
        self,
        url: str,
        outpath: os.PathLike[str],
    ) -> str:
        """Download the compressed file from upstream URL and return its BLAKE2b hash."""
        response = requests.get(url, stream=True, timeout=TIMEOUT)
        response.raise_for_status()
        with Path(outpath).open("wb") as f:
            f.writelines(response.iter_content(chunk_size=8192))

        return get_file_blake2b(outpath)

    def unpack(
        self,
        file: os.PathLike[str] | str,
        folder: os.PathLike[str] | str,
    ) -> dict[str, str]:
        """Extract compressed files."""
        file = Path(file)
        folder = Path(folder)
        compressed_file = self.get_compressed_file_name()

        if not file.is_file():
            msg = f"compressed file not found: {file.name!r}"
            raise ValueError(msg)
        tmp_dir = file.parent

        license_file: Path | None = None
        lib_file: Path | None = None
        # Linux
        if compressed_file.endswith(".zip") and self.platform == "linux":
            with ZipFile(file) as fd:
                license_file = folder / "LICENSE"
                fd.extract("LICENSE", tmp_dir)
                shutil.move(os.fspath(tmp_dir / "LICENSE"), os.fspath(license_file))

                lib_file = folder / "libmediainfo.so.0"
                fd.extract("lib/libmediainfo.so.0.0.0", tmp_dir)
                shutil.move(os.fspath(tmp_dir / "lib/libmediainfo.so.0.0.0"), os.fspath(lib_file))

        # macOS
        elif compressed_file.endswith(".tar.bz2") and self.platform == "darwin":
            with tarfile.open(file) as fd:
                kwargs: dict[str, Any] = {}
                # Set for security reasons, see
                # https://docs.python.org/3/library/tarfile.html#tarfile-extraction-filter
                if sys.version_info >= (3, 12):
                    kwargs = {"filter": "data"}

                license_file = folder / "License.html"
                fd.extract("MediaInfoLib/License.html", tmp_dir, **kwargs)
                shutil.move(
                    os.fspath(tmp_dir / "MediaInfoLib/License.html"),
                    os.fspath(license_file),
                )

                lib_file = folder / "libmediainfo.0.dylib"
                fd.extract("MediaInfoLib/libmediainfo.0.dylib", tmp_dir, **kwargs)
                shutil.move(
                    os.fspath(tmp_dir / "MediaInfoLib/libmediainfo.0.dylib"),
                    os.fspath(lib_file),
                )

        # Windows
        elif compressed_file.endswith(".zip") and self.platform == "win32":
            with ZipFile(file) as fd:
                license_file = folder / "License.html"
                fd.extract("Developers/License.html", tmp_dir)
                shutil.move(os.fspath(tmp_dir / "Developers/License.html"), os.fspath(license_file))

                lib_file = folder / "MediaInfo.dll"
                fd.extract("MediaInfo.dll", tmp_dir)
                shutil.move(os.fspath(tmp_dir / "MediaInfo.dll"), os.fspath(lib_file))

        files = {}
        if license_file is not None and license_file.is_file():
            files["license"] = os.fspath(license_file.relative_to(folder))
        if lib_file is not None and lib_file.is_file():
            files["lib"] = os.fspath(lib_file.relative_to(folder))

        return files

    def download(
        self,
        folder: os.PathLike[str] | str,
        expected_hash: str,
    ) -> dict[str, str]:
        """Download the library and license files, checking the BLAKE2b hash of the archive."""
        folder = Path(folder)

        url = self.get_url()
        compressed_file = self.get_compressed_file_name()

        extracted_files = {}
        with TemporaryDirectory() as tmp_dir:
            outpath = Path(tmp_dir) / compressed_file
            print(f"Downloading MediaInfo library from {url}")
            downloaded_hash = self.download_upstream(url, outpath)
            if downloaded_hash != expected_hash:
                msg = (
                    f"hash mismatch for {compressed_file}: "
                    f"expected {expected_hash}, got {downloaded_hash}"
                )
                raise ValueError(msg)

            print(f"Extracting {compressed_file}")
            extracted_files = self.unpack(outpath, folder)

            print(f"Extracted files: {extracted_files}")
        return extracted_files


def download_files(
    folder: os.PathLike[str] | str,
    platform: Platform,
    arch: Arch,
) -> dict[str, str]:
    """Download the library and license files to the output folder."""
    version, hashes = read_bundled_library_config()
    downloader = Downloader(platform=platform, arch=arch, version=version)
    expected_hash = hashes[downloader.get_compressed_file_suffix()]
    return downloader.download(folder, expected_hash)


def clean_files(folder: os.PathLike[str] | str) -> bool:
    """Remove downloaded files in the output folder."""
    folder = Path(folder)
    if not folder.is_dir():
        print(f"folder does not exist: {os.fspath(folder)!r}")
        return False

    glob_patterns = ["License.html", "LICENSE", "MediaInfo.dll", "libmediainfo.*"]

    # list files to delete
    to_delete: list[Path] = []
    for pattern in glob_patterns:
        to_delete.extend(folder.glob(pattern))

    # delete files
    print(f"will delete files: {to_delete}")
    for relative_path in to_delete:
        (folder / relative_path).unlink()

    return True


if __name__ == "__main__":
    import argparse

    default_folder = Path(__file__).resolve().parent.parent / "src" / "pymediainfo"

    parser = argparse.ArgumentParser(
        description="download MediaInfo files from upstream.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-p",
        "--platform",
        choices=["linux", "darwin", "win32"],
        help="platform of the library",
    )
    parser.add_argument(
        "-a",
        "--arch",
        choices=["x86_64", "arm64", "i386"],
        help="architecture of the library",
    )
    parser.add_argument(
        "-o",
        "--folder",
        type=Path,
        help="output folder",
        default=default_folder,
    )
    parser.add_argument(
        "-c",
        "--clean",
        action="store_true",
        help="clean the output folder of downloaded files.",
    )

    args = parser.parse_args()

    if not any((args.clean, args.platform and args.arch)):
        parser.error("either -c/--clean or -a/--arch with -p/--platform must be used")

    if not args.folder.is_dir():
        parser.error(f"{args.folder} does not exist or is not a folder")

    # Clean folder
    if args.clean:
        clean_files(args.folder)

    # Download files
    if args.platform is not None and args.arch is not None:
        extracted_files = download_files(
            args.folder,
            args.platform,
            args.arch,
        )

    sys.exit(0)
