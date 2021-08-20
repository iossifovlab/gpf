import requests


class HTTPFile:
    def __init__(self, url: str):
        self.url = url
        self._position = 0
        response = requests.head(self.url)
        self._file_length = int(response.headers["Content-Length"])

    def seek(self, position: int = 0):
        self._position = position

    def read(self, size: int = 0):
        if self._position >= self._file_length:
            return ""

        range_end = self._position + size
        if range_end > self._file_length or size == 0:
            range_end = self._file_length
        headers = {"Range": f"bytes={self._position}-{range_end}"}

        self._position = range_end
        response = requests.get(self.url, headers=headers)
        content = response.content.decode("utf-8")
        print(content)
        return content

    def tell(self):
        return self._position

    def close(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        pass
