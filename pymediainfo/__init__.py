from subprocess import Popen, PIPE
from xml.dom import minidom


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


class MediaInfo(object):

    def __init__(self, xml):
        self.xml_dom = xml
        if isinstance(xml, (str, unicode)):
            self.xml_dom = minidom.parseString(xml)

    @staticmethod
    def parse(filename, environment=ENV_DICT):
        command = "mediainfo -f --Output=XML %s" % filename
        p = Popen(command.split(), stdout=PIPE, stderr=PIPE, env=environment)
        p.wait()
        xml = minidom.parseString(p.stdout.read())
        return MediaInfo(xml)

    def _populate_tracks(self):
        for xml_track in self.xml_dom.getElementsByTagName("track"):
            self._tracks.append(Track(xml_track))

    @property
    def tracks(self):
        if not hasattr(self, "_tracks"):
            self._tracks = []
        if len(self._tracks) == 0:
            self._populate_tracks()
        return self._tracks
