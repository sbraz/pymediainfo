# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os
import sys
import unittest

import pytest

from pymediainfo import MediaInfo

data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

class MediaInfoTest(unittest.TestCase):
    def setUp(self):
        with open(os.path.join(data_dir, 'sample.xml'), 'r') as f:
            self.xml_data = f.read()
        self.mi = MediaInfo(self.xml_data)
    def test_populate_tracks(self):
        self.assertEqual(4, len(self.mi.tracks))
    def test_valid_video_track(self):
        for track in self.mi.tracks:
            if track.track_type == 'Video':
                self.assertEqual('DV', track.codec)
                self.assertEqual('Interlaced', track.scan_type)
                break
    def test_track_integer_attributes(self):
        for track in self.mi.tracks:
            if track.track_type == 'Audio':
                self.assertTrue(isinstance(track.duration, int))
                self.assertTrue(isinstance(track.bit_rate, int))
                self.assertTrue(isinstance(track.sampling_rate, int))
                break
    def test_track_other_attributes(self):
        for track in self.mi.tracks:
            if track.track_type == 'General':
                self.assertEqual(5, len(track.other_file_size))
                self.assertEqual(4, len(track.other_duration))
                break
    def test_load_mediainfo_from_string(self):
        self.assertEqual(4, len(self.mi.tracks))
    def test_getting_attribute_that_doesnot_exist(self):
        self.assertTrue(self.mi.tracks[0].does_not_exist is None)

class MediaInfoInvalidXMLTest(unittest.TestCase):
    def setUp(self):
        with open(os.path.join(data_dir, 'invalid.xml'), 'r') as f:
            self.xml_data = f.read()
    def test_parse_invalid_xml(self):
        mi = MediaInfo(MediaInfo._parse_xml_data_into_dom(self.xml_data))
        self.assertEqual(len(mi.tracks), 0)

class MediaInfoLibraryTest(unittest.TestCase):
    def setUp(self):
        self.mi = MediaInfo.parse(os.path.join(data_dir, "sample.mp4"))
    def test_can_parse_true(self):
        self.assertTrue(MediaInfo.can_parse())
    def test_track_count(self):
        self.assertEqual(len(self.mi.tracks), 3)
    def test_track_types(self):
        self.assertEqual(self.mi.tracks[1].track_type, "Video")
        self.assertEqual(self.mi.tracks[2].track_type, "Audio")
    def test_track_details(self):
        self.assertEqual(self.mi.tracks[1].codec, "AVC")
        self.assertEqual(self.mi.tracks[2].codec, "AAC LC")
        self.assertEqual(self.mi.tracks[1].duration, 958)
        self.assertEqual(self.mi.tracks[2].duration, 980)

class MediaInfoUnicodeXMLTest(unittest.TestCase):
    def setUp(self):
        self.mi = MediaInfo.parse(os.path.join(data_dir, "sample.mkv"))
    def test_parse_file_with_unicode_tags(self):
        self.assertEqual(
            self.mi.tracks[0].title,
            "Dès Noël où un zéphyr haï me vêt de glaçons "
            "würmiens je dîne d’exquis rôtis de bœuf au kir à "
            "l’aÿ d’âge mûr & cætera !"
        )

class MediaInfoUnicodeFileNameTest(unittest.TestCase):
    def setUp(self):
        self.mi = MediaInfo.parse(os.path.join(data_dir, "accentué.txt"))
    def test_parse_unicode_file(self):
        self.assertEqual(len(self.mi.tracks), 1)

class MediaInfoURLTest(unittest.TestCase):
    def setUp(self):
        self.mi = MediaInfo.parse("https://github.com/sbraz/pymediainfo/blob/master/tests/data/sample.mkv?raw=true")
    def test_parse_url(self):
        self.assertEqual(len(self.mi.tracks), 2)

class MediaInfoPathlibTest(unittest.TestCase):
    def setUp(self):
        pathlib = pytest.importorskip("pathlib")
        self.path = pathlib.Path(data_dir) / "sample.mp4"
    def test_parse_pathlib_path(self):
        mi = MediaInfo.parse(self.path)
        self.assertEqual(len(mi.tracks), 3)

class MediaInfoCoverDataTest(unittest.TestCase):
    def setUp(self):
        self.mi = MediaInfo.parse(
                os.path.join(data_dir, "sample_with_cover.mp3"),
                cover_data=True
        )
    def test_parse_cover_data(self):
        self.assertEqual(
                self.mi.tracks[0].cover_data,
                "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAACXBIWXMAAAAAAA"
                "AAAQCEeRdzAAAADUlEQVR4nGP4x8DwHwAE/AH+QSRCQgAAAABJRU5ErkJggg=="
        )
