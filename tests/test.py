import os
import unittest
import xml.etree.ElementTree as ET

from pymediainfo import MediaInfo

dir_name = os.path.dirname(os.path.abspath(__file__))

class MediaInfoTest(unittest.TestCase):

    def setUp(self):
        with open(os.path.join(dir_name, 'data/sample.xml'), 'r') as f:
            self.xml_data = f.read()

    def test_populate_tracks(self):
        xml = ET.fromstring(self.xml_data)
        mi = MediaInfo(xml)
        self.assertEqual(4, len(mi.tracks))

    def test_valid_video_track(self):
        xml = ET.fromstring(self.xml_data)
        mi = MediaInfo(xml)
        for track in mi.tracks:
            if track.track_type == 'Video':
                self.assertEqual('DV', track.codec)
                self.assertEqual('Interlaced', track.scan_type)
                break

    def test_track_integer_attributes(self):
        xml = ET.fromstring(self.xml_data)
        mi = MediaInfo(xml)
        for track in mi.tracks:
            if track.track_type == 'Audio':
                self.assertTrue(isinstance(track.duration, int))
                self.assertTrue(isinstance(track.bit_rate, int))
                self.assertTrue(isinstance(track.sampling_rate, int))
                break

    def test_track_other_attributes(self):
        xml = ET.fromstring(self.xml_data)
        mi = MediaInfo(xml)
        for track in mi.tracks:
            if track.track_type == 'General':
                self.assertEqual(5, len(track.other_file_size))
                self.assertEqual(4, len(track.other_duration))
                break

    def test_load_mediainfo_from_string(self):
        mi = MediaInfo(self.xml_data)
        self.assertEqual(4, len(mi.tracks))

    def test_getting_attribute_that_doesnot_exist(self):
        mi = MediaInfo(self.xml_data)
        self.assertTrue(mi.tracks[0].does_not_exist is None)


class MediaInfoInvalidXMLTest(unittest.TestCase):

    def setUp(self):
        with open(os.path.join(dir_name, 'data/invalid.xml'), 'r') as f:
            self.xml_data = f.read()

    def test_parse_invalid_xml(self):
        mi = MediaInfo(MediaInfo.parse_xml_data_into_dom(self.xml_data))
        self.assertEqual(len(mi.tracks), 0)
