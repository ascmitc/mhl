from enum import Enum
from pathlib import Path, PurePosixPath, PureWindowsPath
import os


class _PathType(Enum):
    UNKNOWN = "unknown"
    WINDOWS = "windows"
    POSIX = "posix"
    MIXED = "mixed"


def _detect_path_type(path: str) -> _PathType:
    windows_delimiters = path.count("\\")
    posix_delimiters = path.count("/")

    if windows_delimiters > 0 and posix_delimiters > 0:
        return _PathType.MIXED
    elif windows_delimiters > 0:
        return _PathType.WINDOWS
    elif posix_delimiters > 0:
        return _PathType.POSIX
    else:
        return _PathType.UNKNOWN


def _convert_local_to_xml_path(path: str, _xml_path_type=_PathType.POSIX) -> str:

    if _xml_path_type == _PathType.POSIX:
        return str(Path(path).as_posix())  # anything to posix

    # debug only, is against the ASC MHL specification:
    elif _xml_path_type == _PathType.WINDOWS:
        if os.name == "posix":  # posix to windows
            return str(PureWindowsPath(PurePosixPath(path)))
        elif os.name == "nt":  # windows to windows
            return path
        else:
            print(f"ERR: Unknown operating system: {os.name}")

    else:
        raise ValueError(f"ERR: Unsupported path type: {_xml_path_type}")


def _convert_xml_to_local_path(path: str, convert_from_windows_paths=False) -> str:

    # detect_windows_path_type: option for robust detection of (wrong) windows xml path

    xml_path_type = _PathType.POSIX
    if convert_from_windows_paths:
        xml_path_type = _detect_path_type(path)
        if xml_path_type == _PathType.MIXED:
            xml_path_type = _PathType.POSIX  # probably a backslash in a path name?
        if xml_path_type == _PathType.UNKNOWN:
            xml_path_type = _PathType.POSIX  # no path delimiters found, so safely assume posix

    if xml_path_type == _PathType.POSIX:
        if os.name == "posix":
            return path
        elif os.name == "nt":
            return str(PureWindowsPath(PurePosixPath(path)))
        else:
            print(f"ERR: Unknown operating system: {os.name}")
            assert 0

    elif xml_path_type == _PathType.WINDOWS:
        if os.name == "posix":
            return PureWindowsPath(path).as_posix()
        elif os.name == "nt":
            return path
        else:
            print(f"ERR: Unknown operating system: {os.name}")
            assert 0

    else:
        raise ValueError(f"ERR: Unsupported path type: {xml_path_type}")
