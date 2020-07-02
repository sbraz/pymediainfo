.. pymediainfo documentation master file, created by

Welcome to pymediainfo's documentation!
=======================================

.. toctree::
  :maxdepth: 1

  pymediainfo

============
Requirements
============

This is a simple wrapper around the MediaInfo library, which you can find
at https://mediaarea.net/en/MediaInfo.

.. note::
  * Without the library, this package **cannot parse media files**,
    which severely limits its functionality.

  * Binary wheels containing a bundled library version are provided for Windows and Mac OS X.

  * Packages are available for `several major Linux distributions <https://repology.org/metapackage/python:pymediainfo>`_.
    They depend on the library most of the time and are the preferred way to use pymediainfo
    on Linux unless a specific version of the package is required.

===============
Using MediaInfo
===============

There isn't much to this library so instead of a lot of documentation it is
probably best to just demonstrate how it works:

Getting information from an image
---------------------------------

.. code-block:: python

  from pymediainfo import MediaInfo

  media_info = MediaInfo.parse("/home/user/image.jpg")
  for track in media_info.tracks:
      if track.track_type == "Image":
          print(f"{track.format} of {track.width}×{track.height} pixels.")

Will return something like:

.. code-block:: none

  JPEG of 828×828 pixels.

Getting information from a video
--------------------------------

.. code-block:: python

  from pprint import pprint
  from pymediainfo import MediaInfo

  media_info = MediaInfo.parse("my_video_file.mp4")
  for track in media_info.tracks:
      if track.track_type == "Video":
          print("Bit rate: {t.bit_rate}, Frame rate: {t.frame_rate}, "
                "Format: {t.format}".format(t=track)
          )
          print("Duration (raw value):", track.duration)
          print("Duration (other values:")
          pprint(track.other_duration)
      elif track.track_type == "Audio":
          print("Track data:")
          pprint(track.to_data())

Will return something like:

.. code-block:: none

  Bit rate: 3117597, Frame rate: 23.976, Format: AVC
  Duration (raw value): 958
  Duration (other values):
  ['958 ms',
   '958 ms',
   '958 ms',
   '00:00:00.958',
   '00:00:00;23',
   '00:00:00.958 (00:00:00;23)']
  Track data:
  {'bit_rate': 236392,
   'bit_rate_mode': 'VBR',
   'channel_layout': 'L R',
   'channel_positions': 'Front: L R',
   'channel_s': 2,
   'codec_id': 'mp4a-40-2',
   'commercial_name': 'AAC',
   'compression_mode': 'Lossy',
   …
  }


Dumping objects
---------------

In order to make debugging easier, :class:`pymediainfo.MediaInfo`
and :class:`pymediainfo.Track` objects can be converted to `dict`
using :py:meth:`pymediainfo.MediaInfo.to_data` and
:py:meth:`pymediainfo.Track.to_data` respectively. The previous
example demonstrates that.

Parsing existing MediaInfo output
---------------------------------

If you already have the XML data in a string in memory (e.g. you have previously
parsed the file or were sent the dump from ``mediainfo --output=OLDXML`` by someone
else), you can call the constructor directly:

.. code-block:: python

 from pymediainfo import MediaInfo
 media_info = MediaInfo(raw_xml_string)

Accessing Track attributes
--------------------------

Since the attributes on the :class:`pymediainfo.Track` objects are being dynamically added as the
XML output from MediaInfo is being parsed, there isn't a firm definition of what
will be available at runtime.  In order to make consuming the objects easier so
that you can avoid having to use `hasattr` or `try/except` blocks, the
`__getattribute__` method has been overriden and will just return `None` when
and if an attribute is referenced but doesn't exist.

This will enable you to write consuming code like:

.. code-block:: python

 from pymediainfo import MediaInfo
 media_info = MediaInfo.parse("my_video_file.mp4")
 for track in media_info.tracks:
     if track.bit_rate is None:
         print("""{} tracks do not have bit rate
                  associated with them.""".format(track.track_type))
     else:
         print("{}: {}".format(track.track_type, track.bit_rate))

Output:

.. code-block:: text

 General tracks do not have bit rate associated with them.
 Video: 46033920
 Audio: 1536000
 Menu tracks do not have bit rate associated with them.

=======================
Reporting Issues / Bugs
=======================

Please use the issue tracker in GitHub at https://github.com/sbraz/pymediainfo/issues
to report all feature requests or bug reports. Thanks!


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
