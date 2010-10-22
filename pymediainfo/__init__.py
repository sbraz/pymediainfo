from subprocess import Popen
from xml.dom import minidom
import simplejson
import os
from xml.parsers.expat import ExpatError
from tempfile import mkstemp

__version__ = '1.3.2'

ENV_DICT = {
    "PATH": "/usr/local/bin/:/usr/bin/",
    "LD_LIBRARY_PATH": "/usr/local/lib/:/usr/lib/"}


class Track(object):

    def __getattribute__(self, name):
        try:
            return object.__getattribute__(self, name)
        except:
            pass
        return None

    def __init__(self, xml_dom_fragment):
        self.xml_dom_fragment = xml_dom_fragment
        self.track_type = self.xml_dom_fragment.attributes['type'].value
        for el in self.xml_dom_fragment.childNodes:
            if el.nodeType == 1:
                node_name = el.nodeName.lower().strip().strip('_')
                if node_name == 'id':
                    node_name = 'track_id'
                node_value = el.firstChild.nodeValue
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

    def to_data(self):
        data = {}
        for k, v in self.__dict__.iteritems():
            if k != 'xml_dom_fragment':
                data[k] = v
        return data


class MediaInfo(object):

    def __init__(self, xml):
        self.xml_dom = xml
        if isinstance(xml, (str, unicode)):
            self.xml_dom = MediaInfo.parse_xml_data_into_dom(xml)

    @staticmethod
    def parse_xml_data_into_dom(xml_data):
        dom = None
        try:
            dom = minidom.parseString(xml_data)
        except ExpatError:
            try:
                dom = minidom.parseString(xml_data.replace("<>00:00:00:00</>", ""))
            except:
                pass
        except:
            pass
        return dom

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
        return MediaInfo(xml_dom)

    def _populate_tracks(self):
        if self.xml_dom is None:
            return
        for xml_track in self.xml_dom.getElementsByTagName("track"):
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
        return simplejson.dumps(self.to_data())
