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
at https://mediaarea.net/en/MediaInfo

Binary wheels containing the library are provided for Windows and Mac OS X.

Packages are available for `several Linux distributions <https://repology.org/metapackage/python:pymediainfo>`_.

===============
Using MediaInfo
===============

There isn't much to this library so instead of a lot of documentation it is
probably best to just demonstrate how it works:

.. code-block:: python

 from pymediainfo import MediaInfo
 media_info = MediaInfo.parse('my_video_file.mov')
 for track in media_info.tracks:
     if track.track_type == 'Video':
         print(track.bit_rate, track.bit_rate_mode, track.codec)
 
 # output: 46033920 CBR DV

If you already have the XML data in a string in memory (e.g. you have previously
parsed the file or were sent the dump from `mediainfo` from someone else) you
can call the constructor directly:

.. code-block:: python

 from pymediainfo import MediaInfo
 media_info = MediaInfo(raw_xml_string)

Since the attributes on the `Track` objects are being dynamically added as the
XML output from MediaInfo is being parsed, there isn't a firm definition of what
will be available at runtime.  In order to make consuming the objects easier so
that you can avoid having to use `hasattr` or `try/except` blocks, the
`__getattribute__` method has been overriden and will just return `None` when
and if an attribute is referenced but doesn't exist.

This will enable you to write consuming code like:

.. code-block:: python

 from pymediainfo import MediaInfo
 media_info = MediaInfo.parse('my_video_file.mov')
 for track in media_info.tracks:
     if track.bit_rate is not None:
         print("{}: {}".format(track.track_type, track.bit_rate))
     else:
         print("""{} tracks do not have bit rate
                  associated with them.""".format(track.track_type))

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

