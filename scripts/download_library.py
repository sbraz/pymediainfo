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
import tqdm

if TYPE_CHECKING:
    from typing import Literal


#: Base URL for downloading MediaInfo library
BASE_URL: str = "https://mediaarea.net/download/binary/libmediainfo0"

#: Version of the bundled MediaInfo library
MEDIAINFO_VERSION: str = "24.06"

#: Hashes for the specific MediaInfo version, given the (platform, arch)
MEDIAINFO_HASHES: dict[tuple[str, str], str] = {
    ("linux", "x86_64"): "a2935d6cd937709c4c3b616a71e947f2d99ffd23297c53f3c6a4c985a1563e8e",
    ("linux", "arm64"): "46cdc6a6f366cad60c8dea9b6c592ace8e24f27e7d64c1214ee3ee02365d7f9d",
    ("darwin", "x86_64"): "5298157cf67b52cb65b460242d5477200e54182d5dd31196636b7cf595f6f80f",
    ("darwin", "arm64"): "5298157cf67b52cb65b460242d5477200e54182d5dd31196636b7cf595f6f80f",
    ("win32", "x86_64"): "c14b9d67b3855229cfc556cff3c03e1d27640903602bec6f2153f3269760f0c1",
    ("win32", "i386"): "93922404efe80f8f6e1dd402488445105aa547324baabcf8b3cb38f4996ee0be",
}


def get_file_sha256(file_path: os.PathLike | str, blocksize: int = 1 << 20) -> str:
    """Get the SHA256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        while True:
            data = f.read(blocksize)
            if not data:
                break
            sha256.update(data)
    return sha256.hexdigest()


@dataclass
class Downloader:
    """Downloader for the mediainfo library files."""

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
            msg = f"platform not recognized: {self.platform}"
            raise ValueError(msg)

        # Check the platform and arch is a valid combination
        if allowed_arch is not None and self.arch not in allowed_arch:
            msg = (
                f"for platform {self.platform}, arch {self.arch} is not allowed, "
                f"must be one of {allowed_arch}"
            )
            raise ValueError(msg)

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
            msg = f"platform not recognized: {self.platform}"
            raise ValueError(msg)

        return f"MediaInfo_DLL_{MEDIAINFO_VERSION}_{suffix}"

    def get_url(self) -> str:
        """Get the url to download the mediainfo library."""
        compressed_file = self.get_compressed_file_name()
        return f"{BASE_URL}/{MEDIAINFO_VERSION}/{compressed_file}"

    def compare_hash(self, h: str) -> bool:
        """Compare downloaded hash with expected."""
        key = (self.platform, self.arch)
        expected = MEDIAINFO_HASHES.get(key)
        # Check expected hash exists
        if expected is None:
            msg = f"{key}, expected hash not found."
            raise ValueError(msg)

        # Check hashes match
        if expected != h:
            msg = f"{key}, hash is different from expected: {h}"
            raise ValueError(msg)

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
            for chunk in tqdm.tqdm(response.iter_content(chunk_size=8192), disable=not verbose):
                f.write(chunk)

        downloaded_hash = get_file_sha256(outpath)
        self.compare_hash(downloaded_hash)

    def unzip(
        self,
        file: os.PathLike | str,
        folder: os.PathLike | str,
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

        # MacOS (darwin)
        elif compressed_file.endswith(".tar.bz2") and self.platform == "darwin":
            with tarfile.open(file) as fd:
                kwargs: dict[str, Any] = {}
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
                print(f"Downloading mediainfo library: {compressed_file}")
            self.download_upstream(url, outpath, timeout=timeout, verbose=verbose)

            if verbose:
                print(f"Extract {compressed_file}")
            extracted_files = self.unzip(outpath, folder)

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
    to_delete = []
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

    default_folder = Path(__file__).parent.parent.resolve() / "src" / "pymediainfo"

    parser = argparse.ArgumentParser(description="download MediaInfo files from upstream.")
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
        "--auto",
        action="store_true",
        help="use the current platform and arch",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        help="print information.",
        action="store_true",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        help="url request timeout",
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

    if args.auto:
        args.platform = platform.system().lower()
        args.arch = platform.machine().lower()

    # Clean folder
    if args.clean:
        clean_files(args.folder, verbose=args.verbose)

    # Download files
    if args.platform is not None and args.arch is not None:
        extracted_files = download_files(
            args.folder,
            args.platform,
            args.arch,
            verbose=args.verbose,
            timeout=args.timeout,
        )

    sys.exit(0)
