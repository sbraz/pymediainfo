#!/usr/bin/env python3
"""
a demo that shows how to call pymediainfo
"""

import sys
from pprint import pprint

from pymediainfo import MediaInfo


def print_frame(text):
    print("+-{}-+".format("-" * len(text)))
    print("| {} |".format(text))
    print("+-{}-+".format("-" * len(text)))


def process(fname):
    media_info = MediaInfo.parse(fname)
    for track in media_info.tracks:
        print_frame(track.track_type)
        pprint(track.to_data())
    print()
    for track in media_info.tracks:
        if track.track_type == 'General' and track.duration:
            print("Duration: {} sec.".format(track.duration / 1000.0))


if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("Usage: {} <media_file>".format(sys.argv[0]))
        sys.exit(0)
    process(sys.argv[1])
