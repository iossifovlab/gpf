# pylint: skip-file
# type: ignore

try:
    from .__build__ import VERSION
    __version__ = VERSION
except ImportError:
    from . import _version
    __version__ = _version.get_versions()["version"]
