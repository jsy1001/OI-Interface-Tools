from pbr.version import VersionInfo

_v = VersionInfo('OI-Interface-Tools').semantic_version()
__version__ = _v.release_string()
