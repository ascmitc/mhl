"""
__author__ = "Patrick Renner"
__copyright__ = "Copyright 2024, Pomfort GmbH"

__license__ = "MIT"
__maintainer__ = "Patrick Renner, Alexander Sahm"
__email__ = "opensource@pomfort.com"
"""

import os
from freezegun import freeze_time
from click.testing import CliRunner

from ascmhl.history import MHLHistory
import ascmhl.commands
from ascmhl.paths import _convert_local_to_xml_path, _detect_path_type, _convert_xml_to_local_path, _PathType

from pathlib import Path, PurePosixPath, PureWindowsPath, PosixPath, WindowsPath
import os


def test_conversion_to_posix(fs):
    windows_path = "\\foo\\bar\\test.txt"

    converted_path = PureWindowsPath(windows_path).as_posix()

    assert converted_path == "/foo/bar/test.txt"


def test_conversion_to_windows(fs):
    posix_path = "/foo/bar/test.txt"

    converted_path = str(PureWindowsPath(PurePosixPath(posix_path)))

    assert converted_path == "\\foo\\bar\\test.txt"


def test_detect_path_type():

    windows_path = "\\foo\\bar\\test.txt"
    posix_path = "/foo/bar/test.txt"
    mixed_path = "/foo/bar/test\\file.txt"
    no_path = "file.txt"

    assert _detect_path_type(windows_path) == _PathType.WINDOWS
    assert _detect_path_type(posix_path) == _PathType.POSIX
    assert _detect_path_type(mixed_path) == _PathType.MIXED
    assert _detect_path_type(no_path) == _PathType.UNKNOWN


def test_convert_to_xml_path():

    windows_path = "\\foo\\bar\\test.txt"
    posix_path = "/foo/bar/test.txt"

    if os.name == "posix":
        assert posix_path == _convert_local_to_xml_path(posix_path)
        assert windows_path == _convert_local_to_xml_path(
            posix_path, _xml_path_type=_PathType.WINDOWS
        )  # not a real case, just for debugging
    elif os.name == "nt":
        assert posix_path == _convert_local_to_xml_path(windows_path)
        assert windows_path == _convert_local_to_xml_path(
            windows_path, _xml_path_type=_PathType.WINDOWS
        )  # not a real case, just for debugging
    else:
        print(f"ERR: Unknown operating system: {os.name}")
        assert 0


def test_convert_xml_to_local_path():

    windows_path = "\\foo\\bar\\test.txt"
    posix_path = "/foo/bar/test.txt"

    if os.name == "posix":
        assert posix_path == _convert_xml_to_local_path(posix_path)
        assert posix_path == _convert_xml_to_local_path(
            windows_path, convert_from_windows_paths=True
        )  # robustness for possibly wrong windows paths in XML
        assert posix_path == _convert_xml_to_local_path(
            posix_path, convert_from_windows_paths=True
        )  # should still work
    elif os.name == "nt":
        assert windows_path == _convert_xml_to_local_path(posix_path)
        assert windows_path == _convert_xml_to_local_path(
            windows_path, convert_from_windows_paths=True
        )  # robustness for possibly wrong windows paths in XML
        assert windows_path == _convert_xml_to_local_path(
            posix_path, convert_from_windows_paths=True
        )  # should still work
    else:
        print(f"ERR: Unknown operating system: {os.name}")
        assert 0
