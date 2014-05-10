import json
import os
import sys

from subprocess import Popen
from tempfile import mkstemp

from bs4 import BeautifulSoup, NavigableString

_py3 = sys.version_info >= (3,)

__version__ = '1.4.0'

ENV_DICT = os.environ


class Track(object):

    def __getattribute__(self, name):
        try:
            return object.__getattribute__(self, name)
        except:
            pass
        return None

    def __init__(self, xml_dom_fragment):
        self.xml_dom_fragment = xml_dom_fragment
        self.track_type = xml_dom_fragment.attrs['type']
        for el in self.xml_dom_fragment.children:
            if not isinstance(el, NavigableString):
                node_name = el.name.lower().strip().strip('_')
                if node_name == 'id':
                    node_name = 'track_id'
                node_value = el.string
                other_node_name = "other_%s" % node_name
                if getattr(self, node_name) is None:
                    setattr(self, node_name, node_value)
                else:
                    if getattr(self, other_node_name) is None:
                        setattr(self, other_node_name, [node_value, ])
                    else:
                        getattr(self, other_node_name).append(node_value)

        for o in [d for d in self.__dict__.keys() if d.startswith('other_')]:
            try:
                primary = o.replace('other_', '')
                setattr(self, primary, int(getattr(self, primary)))
            except:
                for v in getattr(self, o):
                    try:
                        current = getattr(self, primary)
                        setattr(self, primary, int(v))
                        getattr(self, o).append(current)
                        break
                    except:
                        pass

    def __repr__(self):
        return("<Track track_id='{0}', track_type='{1}'>".format(self.track_id, self.track_type))

    def to_data(self):
        data = {}
        for k, v in self.__dict__.iteritems():
            if k != 'xml_dom_fragment':
                data[k] = v
        return data


class MediaInfo(object):

    def __init__(self, xml):
        self.xml_dom = xml
        if _py3: xml_types = (str,)     # no unicode type in python3
        else: xml_types = (str, unicode)

        if isinstance(xml, xml_types):
            self.xml_dom = MediaInfo.parse_xml_data_into_dom(xml)

    @staticmethod
    def parse_xml_data_into_dom(xml_data):
        return BeautifulSoup(xml_data, "xml")

    @staticmethod
    def parse(filename, environment=ENV_DICT):
        command = ["mediainfo", "-f", "--Output=XML", filename]
        fileno_out, fname_out = mkstemp(suffix=".xml", prefix="media-")
        fileno_err, fname_err = mkstemp(suffix=".err", prefix="media-")
        fp_out = os.fdopen(fileno_out, 'r+b')
        fp_err = os.fdopen(fileno_err, 'r+b')
        p = Popen(command, stdout=fp_out, stderr=fp_err, env=environment)
        p.wait()
        fp_out.seek(0)

        xml_dom = MediaInfo.parse_xml_data_into_dom(fp_out.read())
        fp_out.close()
        fp_err.close()
        os.unlink(fname_out)
        os.unlink(fname_err)
        return MediaInfo(xml_dom)

    def _populate_tracks(self):
        if self.xml_dom is None:
            return
        for xml_track in self.xml_dom.Mediainfo.File.find_all("track"):
            self._tracks.append(Track(xml_track))

    @property
    def tracks(self):
        if not hasattr(self, "_tracks"):
            self._tracks = []
        if len(self._tracks) == 0:
            self._populate_tracks()
        return self._tracks

    def to_data(self):
        data = {'tracks': []}
        for track in self.tracks:
            data['tracks'].append(track.to_data())
        return data

    def to_json(self):
        return json.dumps(self.to_data())
