import requests
from io import RawIOBase, SEEK_SET, SEEK_CUR, SEEK_END, BufferedRandom, \
    DEFAULT_BUFFER_SIZE


class HTTPRawIO(RawIOBase):
    def __init__(self, url: str):
        self.url = url
        self._position = 0
        response = requests.head(self.url)
        self._file_length = int(response.headers["Content-Length"])

    def seek(self, offset: int, whence=SEEK_SET):
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
        if self.closed:
            raise ValueError("ValueError: I/O operation on closed HTTP file.")
        if self._position >= self._file_length:
            return ""

        range_end = self._position + size
        if range_end > self._file_length or size == -1:
            range_end = self._file_length
        headers = {"Range": f"bytes={int(self._position)}-{int(range_end)}"}

        self._position = range_end
        response = requests.get(self.url, headers=headers)
        content = response.content

        return content

    def readall(self):
        self.seek(0)
        return self.read()

    def readinto(self, b):
        nbytes = b.nbytes
        content = self.read(nbytes-1)
        for idx, a in enumerate(content):
            b[idx] = a
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
