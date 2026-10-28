#!/usr/bin/env python3

# ruff: noqa: T201
"""Tags all pure Python wheels from the 'dist' folder."""

import argparse
import pathlib
import subprocess
import sys

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("platform_tag", help="the tag to add")
    args = parser.parse_args()

    for wheel_path in pathlib.Path("dist").glob("*-py3-none-any.whl"):
        # wheel has no public Python API, use its command line interface
        result = subprocess.run(  # noqa: S603
            [
                sys.executable,
                "-m",
                "wheel",
                "tags",
                "--remove",
                "--platform-tag",
                args.platform_tag,
                str(wheel_path),
            ],
            check=True,
            stdout=subprocess.PIPE,
            text=True,
        )
        print(f"Tagged {wheel_path.name} -> {result.stdout.strip()}")
