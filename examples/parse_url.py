#!/usr/bin/env python3
# ruff: noqa: D102, T201
"""Parse files over HTTP(S) with requests instead of MediaInfo's libcurl."""

import argparse
import io
from http import HTTPStatus
from typing import TYPE_CHECKING

import requests

from pymediainfo import MediaInfo

if TYPE_CHECKING:
    from _typeshed import WriteableBuffer


class HTTPFile(io.RawIOBase):
    """Read-only file object that reads a URL with HTTP range requests."""

    def __init__(self, url: str) -> None:
        self.position = 0
        self.session = requests.Session()
        # Offsets and sizes must apply to the file itself, not a compressed version of it
        self.session.headers["Accept-Encoding"] = "identity"
        self.response: requests.Response | None = None
        response = self.session.head(url, allow_redirects=True, timeout=30)
        response.raise_for_status()
        if response.headers.get("Accept-Ranges") != "bytes":
            msg = f"{url} doesn't support range requests"
            raise OSError(msg)
        # Skip the redirects in later requests
        self.url = response.url
        self.size = int(response.headers["Content-Length"])

    def readable(self) -> bool:
        return True

    def seekable(self) -> bool:
        return True

    def tell(self) -> int:
        return self.position

    def seek(self, offset: int, whence: int = io.SEEK_SET) -> int:
        """Move to a new position, which the next read starts a request from."""
        if whence == io.SEEK_SET:
            position = offset
        elif whence == io.SEEK_CUR:
            position = self.position + offset
        else:  # io.SEEK_END
            position = self.size + offset
        position = max(0, position)
        # Keep the current request if the position doesn't change
        if position != self.position and self.response is not None:
            self.response.close()
            self.response = None
        self.position = position
        return position

    def readinto(self, buffer: "WriteableBuffer", /) -> int:
        """Read from the current request, starting one if needed."""
        # Servers reject ranges that start at or past the end with 416
        if self.position >= self.size:
            return 0
        if self.response is None:
            # The range is open-ended, but with stream=True, only what's read below is
            # downloaded, and seek() closes the response to drop the rest
            self.response = self.session.get(
                self.url, headers={"Range": f"bytes={self.position}-"}, stream=True, timeout=30
            )
            self.response.raise_for_status()
            if self.response.status_code != HTTPStatus.PARTIAL_CONTENT:
                msg = f"{self.url} ignored the range request"
                raise OSError(msg)
        # Cast the buffer to bytes, whatever its format, so that len() and slices count bytes
        view = memoryview(buffer).cast("B")
        data = self.response.raw.read(len(view))
        view[: len(data)] = data
        self.position += len(data)
        return len(data)

    def close(self) -> None:
        """Close the request and the session."""
        if self.response is not None:
            self.response.close()
        self.session.close()
        super().close()


def process(url: str) -> None:
    """Process the URL."""
    print(f"Processing {url}")
    with HTTPFile(url) as file:
        media_info = MediaInfo.parse(file)
    for track in media_info.tracks:
        print(track.track_type, track.format, (track.other_duration or [""])[0])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url", nargs="+", help="URLs to parse")
    args = parser.parse_args()
    for url in args.url:
        process(url)
