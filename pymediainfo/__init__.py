# vim: set fileencoding=utf-8 :
import os
import re
import locale
import json
import ctypes
import sys
import warnings
from pkg_resources import get_distribution, DistributionNotFound
import xml.etree.ElementTree as ET

try:
    import pathlib
except ImportError:
    pathlib = None

if sys.version_info < (3,):
    import urlparse
else:
    import urllib.parse as urlparse

try:
    __version__ = get_distribution("pymediainfo").version
except DistributionNotFound:
    pass

class Track(object):
    """
    An object associated with a media file track.

    Each :class:`Track` attribute corresponds to attributes parsed from MediaInfo's output.
    All attributes are lower case. Attributes that are present several times such as Duration
    yield a second attribute starting with `other_` which is a list of all alternative attribute values.

    When a non-existing attribute is accessed, `None` is returned.

    Example:

    >>> t = mi.tracks[0]
    >>> t
    <Track track_id='None', track_type='General'>
    >>> t.duration
    3000
    >>> t.to_data()["other_duration"]
    ['3 s 0 ms', '3 s 0 ms', '3 s 0 ms',
        '00:00:03.000', '00:00:03.000']
    >>> type(t.non_existing)
    NoneType

    All available attributes can be obtained by calling :func:`to_data`.
    """
    def __eq__(self, other):
        return self.__dict__ == other.__dict__
    def __getattribute__(self, name):
        try:
            return object.__getattribute__(self, name)
        except:
            pass
        return None
    def __getstate__(self):
        return self.__dict__
    def __setstate__(self, state):
        self.__dict__ = state
    def __init__(self, xml_dom_fragment):
        self.track_type = xml_dom_fragment.attrib['type']
        for el in xml_dom_fragment:
            node_name = el.tag.lower().strip().strip('_')
            if node_name == 'id':
                node_name = 'track_id'
            node_value = el.text
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
        return("<Track track_id='{}', track_type='{}'>".format(self.track_id, self.track_type))
    def to_data(self):
        """
        Returns a dict representation of the track attributes.

        Example:

        >>> sorted(track.to_data().keys())[:3]
        ['codec', 'codec_extensions_usually_used', 'codec_url']
        >>> t.to_data()["file_size"]
        5988


        :rtype: dict
        """
        data = {}
        for k, v in self.__dict__.items():
            if k != 'xml_dom_fragment':
                data[k] = v
        return data


class MediaInfo(object):
    """
    An object containing information about a media file.


    :class:`MediaInfo` objects can be created by directly calling code from
    libmediainfo (in this case, the library must be present on the system):

    >>> pymediainfo.MediaInfo.parse("/path/to/file.mp4")

    Alternatively, objects may be created from MediaInfo's XML output.
    Such output can be obtained using the ``XML`` output format on versions older than v17.10
    and the ``OLDXML`` format on newer versions.

    Using such an XML file, we can create a :class:`MediaInfo` object:

    >>> with open("output.xml") as f:
    ...     mi = pymediainfo.MediaInfo(f.read())

    :param str xml: XML output obtained from MediaInfo.
    :param str encoding_errors: option to pass to :func:`str.encode`'s `errors`
        parameter before parsing `xml`.
    :raises xml.etree.ElementTree.ParseError: if passed invalid XML.
    :var tracks: A list of :py:class:`Track` objects which the media file contains.
        For instance:

        >>> mi = pymediainfo.MediaInfo.parse("/path/to/file.mp4")
        >>> for t in mi.tracks:
        ...     print(t)
        <Track track_id='None', track_type='General'>
        <Track track_id='1', track_type='Text'>
    """
    def __eq__(self, other):
        return self.tracks == other.tracks
    def __init__(self, xml, encoding_errors="strict"):
        xml_dom = ET.fromstring(xml.encode("utf-8", encoding_errors))
        self.tracks = []
        # This is the case for libmediainfo < 18.03
        # https://github.com/sbraz/pymediainfo/issues/57
        # https://github.com/MediaArea/MediaInfoLib/commit/575a9a32e6960ea34adb3bc982c64edfa06e95eb
        if xml_dom.tag == "File":
            xpath = "track"
        else:
            xpath = "File/track"
        for xml_track in xml_dom.iterfind(xpath):
            self.tracks.append(Track(xml_track))
    @staticmethod
    def _normalize_filename(filename):
        if hasattr(os, "PathLike") and isinstance(filename, os.PathLike):
            return os.fspath(filename)
        if pathlib is not None and isinstance(filename, pathlib.PurePath):
            return str(filename)
        return filename
    @staticmethod
    def _get_library(library_file=None):
        os_is_nt = os.name in ("nt", "dos", "os2", "ce")
        if os_is_nt:
            lib_type = ctypes.WinDLL
        else:
            lib_type = ctypes.CDLL
        if library_file is None:
            if os_is_nt:
                library_names = ("MediaInfo.dll",)
            elif sys.platform == "darwin":
                library_names = ("libmediainfo.0.dylib", "libmediainfo.dylib")
            else:
                library_names = ("libmediainfo.so.0",)
            script_dir = os.path.dirname(__file__)
            # Look for the library file in the script folder
            for library in library_names:
                lib_path = os.path.join(script_dir, library)
                if os.path.isfile(lib_path):
                    # If we find it, don't try any other filename
                    library_names = (lib_path,)
                    break
        else:
            library_names = (library_file,)
        for i, library in enumerate(library_names, start=1):
            try:
                lib = lib_type(library)
                # Define arguments and return types
                lib.MediaInfo_Inform.restype = ctypes.c_wchar_p
                lib.MediaInfo_New.argtypes = []
                lib.MediaInfo_New.restype  = ctypes.c_void_p
                lib.MediaInfo_Option.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_wchar_p]
                lib.MediaInfo_Option.restype = ctypes.c_wchar_p
                lib.MediaInfo_Inform.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
                lib.MediaInfo_Inform.restype = ctypes.c_wchar_p
                lib.MediaInfo_Open.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p]
                lib.MediaInfo_Open.restype = ctypes.c_size_t
                lib.MediaInfo_Open_Buffer_Init.argtypes = [ctypes.c_void_p, ctypes.c_uint64, ctypes.c_uint64,]
                lib.MediaInfo_Open_Buffer_Init.restype = ctypes.c_size_t
                lib.MediaInfo_Open_Buffer_Continue.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_size_t,]
                lib.MediaInfo_Open_Buffer_Continue.restype = ctypes.c_size_t
                lib.MediaInfo_Open_Buffer_Continue_GoTo_Get.argtypes = [ctypes.c_void_p]
                lib.MediaInfo_Open_Buffer_Continue_GoTo_Get.restype = ctypes.c_uint64
                lib.MediaInfo_Open_Buffer_Finalize.argtypes = [ctypes.c_void_p]
                lib.MediaInfo_Open_Buffer_Finalize.restype = ctypes.c_size_t
                lib.MediaInfo_Delete.argtypes = [ctypes.c_void_p]
                lib.MediaInfo_Delete.restype  = None
                lib.MediaInfo_Close.argtypes = [ctypes.c_void_p]
                lib.MediaInfo_Close.restype = None
                # Without a handle, there might be problems when using concurrent threads
                # https://github.com/sbraz/pymediainfo/issues/76#issuecomment-574759621
                handle = lib.MediaInfo_New()
                lib_version_str = lib.MediaInfo_Option(handle, "Info_Version", "")
                lib_version_str = re.search(r"^MediaInfoLib - v(\S+)", lib_version_str).group(1)
                lib_version = tuple(int(_) for _ in lib_version_str.split("."))
                return (lib, handle, lib_version_str, lib_version)
            except OSError:
                # If we've tried all possible filenames
                if i == len(library_names):
                    raise
    @classmethod
    def can_parse(cls, library_file=None):
        """
        Checks whether media files can be analyzed using libmediainfo.

        :rtype: bool
        """
        try:
            lib, handle = cls._get_library(library_file)[:2]
            lib.MediaInfo_Close(handle)
            lib.MediaInfo_Delete(handle)
            return True
        except:
            return False
    @classmethod
    def parse(cls, filename, library_file=None, cover_data=False,
            encoding_errors="strict", parse_speed=0.5, text=False,
            full=True, legacy_stream_display=False, mediainfo_options=None,
            output=None):
        """
        Analyze a media file using libmediainfo.

        .. note::
            Because of the way the underlying library works, this method should not
            be called simultaneously from multiple threads *with different arguments*.
            Doing so will cause inconsistencies or failures by changing
            library options that are shared across threads.

        :param filename: path to the media file or file-like object which will be analyzed.
            A URL can also be used if libmediainfo was compiled
            with CURL support.
        :param str library_file: path to the libmediainfo library, this should only be used if the library cannot be auto-detected.
        :param bool cover_data: whether to retrieve cover data as base64.
        :param str encoding_errors: option to pass to :func:`str.encode`'s `errors`
            parameter before parsing MediaInfo's XML output.
        :param float parse_speed: passed to the library as `ParseSpeed`,
            this option takes values between 0 and 1.
            A higher value will yield more precise results in some cases
            but will also increase parsing time.
        :param bool full: display additional tags, including computer-readable values
            for sizes and durations.
        :param bool legacy_stream_display: display additional information about streams.
        :param dict mediainfo_options: additional options that will be passed to the `MediaInfo_Option` function,
            for example: ``{"Language": "raw"}``. Do not use this parameter when running the
            method simultaneously from multiple threads, it will trigger a reset of all options
            which will cause inconsistencies or failures.
        :param str output: custom output format for MediaInfo, corresponds to the CLI's
            ``--Output`` parameter. Setting this causes the method to
            return a `str` instead of a :class:`MediaInfo` object.

            Useful values include:
                * the empty `str` ``""`` (corresponds to the default
                  text output, obtained when running ``mediainfo`` with no
                  additional parameters)

                * ``"XML"``

                * ``"JSON"``

                * ``%``-delimited templates (see ``mediainfo --Info-Parameters``)
        :type filename: str or pathlib.Path or os.PathLike or file-like object.
        :rtype: str if `output` is set.
        :rtype: :class:`MediaInfo` otherwise.
        :raises FileNotFoundError: if passed a non-existent file.
        :raises IOError: if passed a non-existent file (Python < 3.3).
        :raises ValueError: if passed a file-like object opened in text mode.
        :raises RuntimeError: if parsing fails, this should not
            happen unless libmediainfo itself fails.

        Examples:
            >>> pymediainfo.MediaInfo.parse("tests/data/sample.mkv")
                <pymediainfo.MediaInfo object at 0x7fa83a3db240>

            >>> import json
            >>> mi = pymediainfo.MediaInfo.parse("tests/data/sample.mkv",
            ...     output="JSON")
            >>> json.loads(mi)["media"]["track"][0]
                {'@type': 'General', 'TextCount': '1', 'FileExtension': 'mkv',
                    'FileSize': '5904',  … }


        """
        lib, handle, lib_version_str, lib_version = cls._get_library(library_file)
        # The XML option was renamed starting with version 17.10
        if lib_version >= (17, 10):
            xml_option = "OLDXML"
        else:
            xml_option = "XML"
        # Cover_Data is not extracted by default since version 18.03
        # See https://github.com/MediaArea/MediaInfoLib/commit/d8fd88a1c282d1c09388c55ee0b46029e7330690
        if lib_version >= (18, 3):
            lib.MediaInfo_Option(handle, "Cover_Data", "base64" if cover_data else "")
        lib.MediaInfo_Option(handle, "CharSet", "UTF-8")
        # Fix for https://github.com/sbraz/pymediainfo/issues/22
        # Python 2 does not change LC_CTYPE
        # at startup: https://bugs.python.org/issue6203
        if (sys.version_info < (3,) and os.name == "posix"
                and locale.getlocale() == (None, None)):
            locale.setlocale(locale.LC_CTYPE, locale.getdefaultlocale())
        if text:
            warnings.warn('The "text" option is obsolete and will be removed '
                    'in the next major version. Use output="" instead.',
                    DeprecationWarning
            )
            output = ""
        lib.MediaInfo_Option(handle, "Inform", xml_option if output is None else output)
        lib.MediaInfo_Option(handle, "Complete", "1" if full else "")
        lib.MediaInfo_Option(handle, "ParseSpeed", str(parse_speed))
        lib.MediaInfo_Option(handle, "LegacyStreamDisplay", "1" if legacy_stream_display else "")
        if mediainfo_options is not None:
            if lib_version < (19, 9):
                warnings.warn("This version of MediaInfo ({}) does not support resetting all options to their default values, "
                    "passing it custom options is not recommended and may result in unpredictable behavior, "
                    "see https://github.com/MediaArea/MediaInfoLib/issues/1128".format(lib_version_str),
                    RuntimeWarning
                )
            for option_name, option_value in mediainfo_options.items():
                lib.MediaInfo_Option(handle, option_name, option_value)
        try:
            filename.seek(0, 2)
            file_size = filename.tell()
            filename.seek(0)
        except AttributeError: # filename is not a file-like object
            file_size = None

        if file_size is not None: # We have a file-like object, use the buffer protocol:
            # Some file-like objects do not have a mode
            if "b" not in getattr(filename, "mode", "b"):
                raise ValueError("File should be opened in binary mode")
            lib.MediaInfo_Open_Buffer_Init(handle, file_size, 0)
            while True:
                buffer = filename.read(64 * 1024)
                if buffer:
                    # https://github.com/MediaArea/MediaInfoLib/blob/v20.09/Source/MediaInfo/File__Analyze.h#L1429
                    # 4th bit = finished
                    if lib.MediaInfo_Open_Buffer_Continue(handle, buffer, len(buffer)) & 0x08:
                        break
                    # Ask MediaInfo if we need to seek
                    seek = lib.MediaInfo_Open_Buffer_Continue_GoTo_Get(handle)
                    # https://github.com/MediaArea/MediaInfoLib/blob/v20.09/Source/MediaInfoDLL/MediaInfoJNI.cpp#L127
                    if seek != ctypes.c_uint64(-1).value:
                        filename.seek(seek)
                        # Inform MediaInfo we have sought
                        lib.MediaInfo_Open_Buffer_Init(handle, file_size, filename.tell())
                else:
                    break
            lib.MediaInfo_Open_Buffer_Finalize(handle)
        else: # We have a filename, simply pass it:
            filename = cls._normalize_filename(filename)
            # If an error occured
            if lib.MediaInfo_Open(handle, filename) == 0:
                lib.MediaInfo_Close(handle)
                lib.MediaInfo_Delete(handle)
                # If filename doesn't look like a URL and doesn't exist
                if "://" not in filename and not os.path.exists(filename):
                    try:
                        Error = FileNotFoundError
                    except NameError: # Python 2 compat
                        Error = IOError
                    raise Error(filename)
                # We ran into another kind of error
                raise RuntimeError("An error occured while opening {}"
                                   " with libmediainfo".format(filename))
        info = lib.MediaInfo_Inform(handle, 0)
        # Reset all options to their defaults so that they aren't
        # retained when the parse method is called several times
        # https://github.com/MediaArea/MediaInfoLib/issues/1128
        # Do not call it when it is not required because it breaks threads
        # https://github.com/sbraz/pymediainfo/issues/76#issuecomment-575245093
        if mediainfo_options is not None and lib_version >= (19, 9):
            lib.MediaInfo_Option(handle, "Reset", "")
        # Delete the handle
        lib.MediaInfo_Close(handle)
        lib.MediaInfo_Delete(handle)
        if output is None:
            return cls(info, encoding_errors)
        else:
            return info
    def to_data(self):
        """
        Returns a dict representation of the object's :py:class:`Tracks <Track>`.

        :rtype: dict
        """
        data = {'tracks': []}
        for track in self.tracks:
            data['tracks'].append(track.to_data())
        return data
    def to_json(self):
        """
        Returns a JSON representation of the object's :py:class:`Tracks <Track>`.

        :rtype: str
        """
        return json.dumps(self.to_data())
