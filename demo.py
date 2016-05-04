#!/usr/bin/env python
# encoding: utf-8

"""
a demo that shows how to call pymediainfo
"""

from __future__ import (absolute_import, division,
                        print_function, unicode_literals)

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
    #
    print()
    for track in media_info.tracks:
        if track.track_type == 'General' and track.duration:
            print("Duration: {} sec.".format(track.duration / 1000.0))

##############################################################################

if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("Usage: {} <media_file>".format(sys.argv[0]))
        sys.exit(0)
    if sys.version_info.major < 3:
        process(sys.argv[1].decode(sys.getfilesystemencoding()))
    else:
        process(sys.argv[1])
