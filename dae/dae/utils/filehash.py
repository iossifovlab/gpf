import hashlib


def hashsum(filename, hasher, blocksize=65536):
    with open(filename, "rb") as infile:
        for block in iter(lambda: infile.read(blocksize), b""):
            hasher.update(block)
    return hasher.hexdigest()


def md5sum(filename, blocksize=65536):
    return hashsum(filename, hashlib.md5(), blocksize)


def sha256sum(filename, blocksize=65536):
    return hashsum(filename, hashlib.sha256(), blocksize)
