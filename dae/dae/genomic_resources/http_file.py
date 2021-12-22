import logging
import requests
from io import RawIOBase, SEEK_SET, SEEK_CUR, SEEK_END, BufferedRandom, \
    DEFAULT_BUFFER_SIZE

logger = logging.getLogger(__name__)


class HTTPRawIO(RawIOBase):
    def __init__(self, url: str):
        self.url = url
        self._position = 0
        response = requests.head(self.url)
        self._file_length = int(response.headers["Content-Length"])

    def seek(self, offset: int, whence=SEEK_SET):
        # print(f"IIII seek(offset={offset}, whence={whence})")
        if whence == SEEK_SET:
            self._position = 0 + offset
        elif whence == SEEK_CUR or whence == SEEK_END:
            if whence == SEEK_END and offset > 0:
                offset = -offset
            self._position += offset
        else:
            raise ValueError("Invalid seek")
        return self._position

    def seekable(self):
        return True

    def writable(self):
        return True

    def isatty(self):
        return False

    def readable(self):
        return True

    def read(self, size: int = -1):
        # print(f"IIII read(size={size})")
        if self.closed:
            raise ValueError("ValueError: I/O operation on closed HTTP file.")
        if self._position >= self._file_length:
            return b""

        range_end = self._position + size
        if range_end > self._file_length or size == -1:
            range_end = self._file_length
        headers = {"Range": f"bytes={self._position}-{range_end-1}"}
        # print(f'IIII      header: {headers}')

        self._position = range_end
        response = requests.get(self.url, headers=headers)
        content = response.content

        return content

    def readall(self):
        # print("IIII readall()")
        self.seek(0)
        return self.read()

    def readinto(self, b):
        # print(f"IIII readinto({b.nbytes})")
        nbytes = b.nbytes
        content = self.read(nbytes)
        # print(f"IIII      len(content): {len(content)}")

        # for idx, a in enumerate(content):
        #     b[idx] = a
        b[:len(content)] = content
        return len(content)

    def write(self, b):
        raise NotImplementedError()

    def readline(self, size: int = -1):
        raise NotImplementedError()

    def readlines(self, hint: int = -1):
        raise NotImplementedError()

    def writelines(self, lines):
        raise NotImplementedError()

    def tell(self):
        return self._position


class HTTPFile(BufferedRandom):
    def __init__(self, url: str, buffer_size=DEFAULT_BUFFER_SIZE):
        http_raw_io = HTTPRawIO(url)
        super().__init__(http_raw_io, buffer_size)
