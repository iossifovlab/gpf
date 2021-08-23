import requests


class HTTPFile:
    def __init__(self, url: str):
        self.url = url
        self._position = 0
        response = requests.head(self.url)
        self._file_length = int(response.headers["Content-Length"])
        self.closed = False

    def seek(self, position: int = 0):
        self._position = position

    def read(self, size: int = 0):
        if self.closed:
            raise ValueError("ValueError: I/O operation on closed HTTP file.")

        if self._position >= self._file_length:
            return ""

        range_end = self._position + size
        if range_end > self._file_length or size == 0:
            range_end = self._file_length
        headers = {"Range": f"bytes={int(self._position)}-{int(range_end)}"}

        self._position = range_end
        response = requests.get(self.url, headers=headers)
        content = response.content.decode("utf-8")
        return content

    def tell(self):
        return self._position

    def close(self):
        self.closed = True

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        pass

    def __iter__(self):
        pass
