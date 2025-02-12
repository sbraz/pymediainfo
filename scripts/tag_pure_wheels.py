#!/usr/bin/env python3

# ruff: noqa: T201
"""Tags all pure Python wheels from the 'dist' folder."""

import argparse
import pathlib

from wheel.cli.tags import tags

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("platform_tag", help="the tag to add")
    args = parser.parse_args()

    for wheel_path in pathlib.Path("dist").glob("*-py3-none-any.whl"):
        new_wheel = tags(wheel_path, platform_tags=args.platform_tag, remove=True)
        print(f"Tagged {wheel_path.name} -> {new_wheel}")
