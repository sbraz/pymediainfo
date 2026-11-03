#!/usr/bin/env python3
"""Show a progress bar while parsing whole files."""

import argparse
from pathlib import Path

import rich
import rich.progress
from rich.table import Table

from pymediainfo import MediaInfo


def process(media_file: str) -> None:
    """Process the file."""
    name = Path(media_file).name
    # rich.progress.open() returns a file object that advances the progress
    # bar on each read and moves it on each seek
    with rich.progress.open(media_file, "rb", description=name) as file:
        # parse_speed=1 makes MediaInfo read the whole file instead of
        # skipping parts of it
        media_info = MediaInfo.parse(file, parse_speed=1)
    table = Table("Track", "ID", "Format", "Duration", "Bit rate", title=name)
    for track in media_info.tracks:
        table.add_row(
            track.track_type,
            "" if track.track_id is None else str(track.track_id),
            track.format,
            # The other_* attributes hold the values in human-readable forms
            (track.other_duration or [""])[0],
            # General tracks only have an overall bit rate
            (track.other_bit_rate or track.other_overall_bit_rate or [""])[0],
        )
    rich.print(table)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("media_file", nargs="+", help="media files to parse")
    args = parser.parse_args()
    for media_file in args.media_file:
        process(media_file)
