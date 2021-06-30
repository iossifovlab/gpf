
class Manifest(dict):
    def __init__(self, filestream):
        super().__init__()
        for chunk_raw in filestream:
            chunk = chunk_raw.decode("ascii")
            lines = chunk.split("\n")
            for line in lines:
                if(len(line)):
                    line_split = line.split(" ")
                    checksum = line_split[0]
                    filename = line_split[1]
                    self[filename] = checksum
