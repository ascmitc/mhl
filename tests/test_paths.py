"""
__author__ = "Patrick Renner"
__copyright__ = "Copyright 2024, Pomfort GmbH"

__license__ = "MIT"
__maintainer__ = "Patrick Renner, Alexander Sahm"
__email__ = "opensource@pomfort.com"
"""

from .conftest import abspath_conversion_tests
from ascmhl.utils import convert_local_path_to_posix, convert_posix_to_local_path

from pathlib import PurePosixPath, PureWindowsPath
from .conftest import path_conversion_tests
import os


def test_conversion_to_posix(fs):
    windows_path = "\\foo\\bar\\test.txt"

    converted_path = PureWindowsPath(windows_path).as_posix()

    assert converted_path == "/foo/bar/test.txt"


def test_conversion_to_windows(fs):
    posix_path = "/foo/bar/test.txt"

    converted_path = str(PureWindowsPath(PurePosixPath(posix_path)))

    assert converted_path == "\\foo\\bar\\test.txt"


def test_conversion_from_posix_to_local():
    posix_path = "/foo/bar/test.txt"

    converted_path = str(path_conversion_tests(posix_path))
    if os.name == "posix":
        assert converted_path == posix_path
    elif os.name == "nt":
        assert converted_path == "\\foo\\bar\\test.txt"


def test_abspath_from_posix():
    # this test is only relevant on windows
    if os.name != "nt":
        return

    posix_path = "/foo/bar/test.txt"
    previous_cwd = os.getcwd()

    # the assumed drive depends on the working directory
    os.chdir("C:\\")
    converted_path = abspath_conversion_tests(posix_path)
    if os.name == "posix":
        assert converted_path == posix_path
    elif os.name == "nt":
        assert converted_path == "C:\\foo\\bar\\test.txt"

    os.chdir("D:\\")
    converted_path = abspath_conversion_tests(posix_path)
    if os.name == "posix":
        assert converted_path == posix_path
    elif os.name == "nt":
        assert converted_path == "D:\\foo\\bar\\test.txt"

    # restore the working directory to avoid influencing other tests
    os.chdir(previous_cwd)


def test_convert_to_xml_path():

    windows_path = "\\foo\\bar\\test.txt"
    posix_path = "/foo/bar/test.txt"

    if os.name == "posix":
        assert posix_path == convert_local_path_to_posix(posix_path)
    elif os.name == "nt":
        assert posix_path == convert_local_path_to_posix(windows_path)
    else:
        print(f"ERR: Unknown operating system: {os.name}")
        assert 0


def test_convert_xml_to_local_path():

    windows_path = "\\foo\\bar\\test.txt"
    posix_path = "/foo/bar/test.txt"

    if os.name == "posix":
        assert posix_path == convert_posix_to_local_path(posix_path)
    elif os.name == "nt":
        assert windows_path == convert_posix_to_local_path(posix_path)
    else:
        print(f"ERR: Unknown operating system: {os.name}")
        assert 0
