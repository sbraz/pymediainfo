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

if TYPE_CHECKING:
    from typing import Literal


#: Base URL for downloading MediaInfo library
BASE_URL: str = "https://mediaarea.net/download/binary/libmediainfo0"

#: Version of the bundled MediaInfo library
MEDIAINFO_VERSION: str = "24.12"

# fmt: off
#: BLAKE2b hashes for the specific MediaInfo version, given the (platform, arch)
MEDIAINFO_HASHES: dict[tuple[str, str], str] = {
    ("linux", "x86_64"): "13c4afb2948187cc06f13b1cd7d7a49f8618b8d1e3a440d9e96ef7b486a653d5e2567aae97dc253e3d3f484a7837e4b5a972abab4803223300a79c601c0bcce1",
    ("linux", "arm64"): "4e5a9826fa987f4bde46a6586894d45f3d5381f25d8886dfef67f5db3a9f4377ecafc12acc6e2d71e43b062b686c2db2523052a1f3dd7505a41091847788d114",
    # The same file is used for darwin x86_64 and arm64 (suffixed Mac_x86_64+arm64.tar.bz2)
    ("darwin", "x86_64"): "65b8195f0859369fa0ab1870cbde1535bb57f16bde451b22585d849c870f1ca92972328c11edd15b6f8187445dd58efff7107cfce39d2be7a88e8c434589b4ae",
    ("darwin", "arm64"): "65b8195f0859369fa0ab1870cbde1535bb57f16bde451b22585d849c870f1ca92972328c11edd15b6f8187445dd58efff7107cfce39d2be7a88e8c434589b4ae",
    ("win32", "x86_64"): "f831c588e9eaf51201b4cc7995dce66852591764fc5ef05effd3a8a2037ff5d37ec039eef5d1f990f05bd7452c1cad720e95b77a095f9f1a690689e351fc00b8",
    ("win32", "i386"): "0f0e14c103eac858fe683ec7d51634d62e5e0af658940fd26608249f1048846a92a334438204fe5ecfceb70cb00e5550bfb717a77f10816a2583b5041bb61790",
}
# fmt: on


def get_file_blake2b(file_path: os.PathLike | str, chunksize: int = 1 << 20) -> str:
    """Get the BLAKE2b hash of a file."""
    blake2b = hashlib.blake2b()
    with open(file_path, "rb") as f:
        while chunk := f.read(chunksize):
            blake2b.update(chunk)
    return blake2b.hexdigest()


@dataclass
class Downloader:
    """Downloader for the MediaInfo library files."""

    platform: Literal["linux", "darwin", "win32"]
    arch: Literal["x86_64", "arm64", "i386"]

    def __post_init__(self) -> None:
        """Check that the combination of platform and arch is allowed."""
        allowed_arch = None
        if self.platform in ("linux", "darwin"):
            allowed_arch = ["x86_64", "arm64"]
        elif self.platform == "win32":
            allowed_arch = ["x86_64", "i386"]
        else:
            raise ValueError(f"platform not recognized: {self.platform}")

        # Check the platform and arch is a valid combination
        if allowed_arch is not None and self.arch not in allowed_arch:
            raise ValueError(
                f"arch {self.arch} is not allowed for platform {self.platform}; "
                f"must be one of {allowed_arch}"
            )

    def get_compressed_file_name(self) -> str:
        """Get the compressed file name."""
        if self.platform == "linux":
            suffix = f"Lambda_{self.arch}.zip"
        elif self.platform == "darwin":
            suffix = "Mac_x86_64+arm64.tar.bz2"
        elif self.platform == "win32":
            win_arch = "x64" if self.arch == "x86_64" else self.arch
            suffix = f"Windows_{win_arch}_WithoutInstaller.zip"
        else:
            raise ValueError(f"platform not recognized: {self.platform}")

        return f"MediaInfo_DLL_{MEDIAINFO_VERSION}_{suffix}"

    def get_url(self) -> str:
        """Get the URL to download the MediaInfo library."""
        compressed_file = self.get_compressed_file_name()
        return f"{BASE_URL}/{MEDIAINFO_VERSION}/{compressed_file}"

    def compare_hash(self, h: str) -> bool:
        """Compare downloaded hash with expected."""
        key = (self.platform, self.arch)
        expected = MEDIAINFO_HASHES.get(key)
        # Check expected hash exists
        if expected is None:
            raise ValueError(f"{key}, expected hash not found.")

        # Check hashes match
        if expected != h:
            raise ValueError(f"hash mismatch for {key}: expected {expected}, got {h}")

        return True

    def download_upstream(
        self,
        url: str,
        outpath: os.PathLike,
        *,
        timeout: int = 20,
        verbose: bool = True,
    ) -> None:
        """Download the compressed file from upstream URL."""
        response = requests.get(url, stream=True, timeout=timeout)
        response.raise_for_status()
        with open(outpath, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        downloaded_hash = get_file_blake2b(outpath)
        self.compare_hash(downloaded_hash)

    def unpack(
        self,
        file: os.PathLike | str,
        folder: os.PathLike | str,
    ) -> dict[str, str]:
        """Extract compressed files."""
        file = Path(file)
        folder = Path(folder)
        compressed_file = self.get_compressed_file_name()

        if not file.is_file():
            raise ValueError(f"compressed file not found: {file.name!r}")
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

        # macOS (darwin)
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

        # Windows (win32)
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
        folder: os.PathLike | str,
        *,
        timeout: int = 20,
        verbose: bool = True,
    ) -> dict[str, str]:
        """Download the library and license files."""
        folder = Path(folder)

        url = self.get_url()
        compressed_file = self.get_compressed_file_name()

        extracted_files = {}
        with TemporaryDirectory() as tmp_dir:
            outpath = Path(tmp_dir) / compressed_file
            if verbose:
                print(f"Downloading MediaInfo library from {url}")
            self.download_upstream(url, outpath, timeout=timeout, verbose=verbose)

            if verbose:
                print(f"Extracting {compressed_file}")
            extracted_files = self.unpack(outpath, folder)

            if verbose:
                print(f"Extracted files: {extracted_files}")
        return extracted_files


def download_files(
    folder: os.PathLike | str,
    platform: Literal["linux", "darwin", "win32"],
    arch: Literal["x86_64", "arm64", "i386"],
    *,
    timeout: int = 20,
    verbose: bool = True,
) -> dict[str, str]:
    """Download the library and license files to the output folder."""
    downloader = Downloader(platform=platform, arch=arch)
    return downloader.download(folder, timeout=timeout, verbose=verbose)


def clean_files(
    folder: os.PathLike | str,
    *,
    verbose: bool = True,
) -> bool:
    """Remove downloaded files in the output folder."""
    folder = Path(folder)
    if not folder.is_dir():
        if verbose:
            print(f"folder does not exist: {os.fspath(folder)!r}")
        return False

    glob_patterns = ["License.html", "LICENSE", "MediaInfo.dll", "libmediainfo.*"]

    # list files to delete
    to_delete: list[os.PathLike] = []
    for pattern in glob_patterns:
        to_delete.extend(folder.glob(pattern))

    # delete files
    if verbose:
        print(f"will delete files: {to_delete}")
    for relative_path in to_delete:
        (folder / relative_path).unlink()

    return True


if __name__ == "__main__":
    import argparse
    import platform

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
        "-A",
        "--auto",
        action="store_true",
        help="use the current platform and architecture",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        help="hide progress messages",
        action="store_true",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        help="URL request timeout in seconds",
        default=20,
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

    if not any((args.auto, args.clean, args.platform and args.arch)):
        parser.error("either -A/--auto, -c/--clean or -a/--arch with -p/--platform must be used")

    if not args.folder.is_dir():
        parser.error(f"{args.folder} does not exist or is not a folder")

    if args.auto:
        args.platform = platform.system().lower()
        args.arch = platform.machine().lower()

    # Clean folder
    if args.clean:
        clean_files(args.folder, verbose=not args.quiet)

    # Download files
    if args.platform is not None and args.arch is not None:
        extracted_files = download_files(
            args.folder,
            args.platform,
            args.arch,
            verbose=not args.quiet,
            timeout=args.timeout,
        )

    sys.exit(0)
