#!/usr/bin/env python3

# ruff: noqa: T201
"""Tags the pure Python wheel from the 'dist' folder for a platform and architecture."""

import argparse
import pathlib
import subprocess
import sys

from download_library import WHEEL_TAGS

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "-p",
        "--platform",
        choices=WHEEL_TAGS,
        required=True,
        help="platform of the library",
    )
    parser.add_argument(
        "-a",
        "--arch",
        choices=["x86_64", "arm64", "i386"],
        required=True,
        help="architecture of the library",
    )
    args = parser.parse_args()

    platform_tag = WHEEL_TAGS[args.platform].get(args.arch)
    if platform_tag is None:
        parser.error(f"no wheel for arch {args.arch} on platform {args.platform}")

    # The dist folder isn't cleared between builds: a pure wheel left from an
    # earlier build may not contain this platform's library
    wheel_paths = list(pathlib.Path("dist").glob("*-py3-none-any.whl"))
    if len(wheel_paths) != 1:
        parser.error(f"expected one pure wheel in dist, found {len(wheel_paths)}")
    wheel_path = wheel_paths[0]

    # wheel has no public Python API, use its command line interface
    result = subprocess.run(  # noqa: S603
        [
            sys.executable,
            "-m",
            "wheel",
            "tags",
            "--remove",
            "--platform-tag",
            platform_tag,
            str(wheel_path),
        ],
        check=True,
        stdout=subprocess.PIPE,
        text=True,
    )
    print(f"Tagged {wheel_path.name} -> {result.stdout.strip()}")
