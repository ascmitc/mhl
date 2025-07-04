"""
__author__ = "Alexander Sahm"
__copyright__ = "Copyright 2020, Pomfort GmbH"

__license__ = "MIT"
__maintainer__ = "Patrick Renner, Alexander Sahm"
__email__ = "opensource@pomfort.com"
"""

import pytest
from freezegun import freeze_time
from click.testing import CliRunner
from os.path import abspath
from pathlib import Path
import ascmhl.commands
import os
import time
import platform

# this file is automatically loaded by pytest we setup various shared fixtures here


def abspath_conversion_tests(path):
    return abspath(path)


def path_conversion_tests(path):
    return Path(path)


# The shutil.rmtree will not work with the fake filesystem on Python 3.12 (because it will not take symlinks),
# so here is an implementation for removing entire directories that will work with the fake fs
def remove_tree(path):
    """Recursively delete a directory tree, correctly handling symbolic links."""
    for root, dirs, files in os.walk(path, topdown=False):
        for name in files:
            file_path = os.path.join(root, name)
            try:
                os.remove(file_path)  # Remove files
            except OSError as e:
                print(f"Error removing file {file_path}: {e}")

        for name in dirs:
            dir_path = os.path.join(root, name)
            try:
                # If it's a symbolic link, just remove the link itself
                if os.path.islink(dir_path):
                    os.remove(dir_path)
                else:
                    os.rmdir(dir_path)  # Remove empty directories
            except OSError as e:
                print(f"Error removing directory {dir_path}: {e}")

    # Finally remove the root directory (if not a symlink)
    if os.path.islink(path):
        os.remove(path)
    else:
        os.rmdir(path)


@pytest.fixture(scope="session", autouse=True)
def set_timezone():
    """Fakes the host timezone to UTC so we don't get different mhl files if the tests run on different time zones
    seems like freezegun can't handle timezones like we want"""
    if not os.name == "nt":
        os.environ["TZ"] = "UTZ"
        time.tzset()
    else:
        os.system('tzutil /s "UTC"')


@pytest.fixture(autouse=True)
def setup_environment(monkeypatch):
    def fake_hostname():
        return "myHost.local"

    monkeypatch.setattr(platform, "node", fake_hostname)
    # TODO: also patch ascmhl_tool_version ?


@pytest.fixture
@freeze_time("2020-01-15 13:00:00")
def nested_mhl_histories(fs):
    # create mhl histories on different directly levels
    fs.create_file("/root/Stuff.txt", contents="stuff\n")
    runner = CliRunner()
    result = runner.invoke(ascmhl.commands.create, [abspath_conversion_tests("/root"), "-h", "xxh64"])
    assert result.exit_code == 0

    fs.create_file("/root/A/AA/AA1.txt", contents="AA1\n")
    fs.create_file("/root/A/AB/AB1.txt", contents="AB1\n")
    result = runner.invoke(ascmhl.commands.create, [abspath_conversion_tests("/root/A/AA"), "-h", "xxh64"])
    assert result.exit_code == 0

    fs.create_file("/root/B/B1.txt", contents="B1\n")
    result = runner.invoke(ascmhl.commands.create, [abspath_conversion_tests("/root/B"), "-h", "xxh64"])
    assert result.exit_code == 0

    fs.create_file("/root/B/BA/BA1.txt", contents="BA1\n")
    fs.create_file("/root/B/BB/BB1.txt", contents="BB1\n")
    result = runner.invoke(ascmhl.commands.create, [abspath_conversion_tests("/root/B/BB"), "-h", "xxh64"])
    assert result.exit_code == 0


@pytest.fixture
@freeze_time("2020-01-15 13:00:00")
def simple_mhl_history(fs):
    # create a simple mhl history with two files in one generation
    fs.create_file("/root/Stuff.txt", contents="stuff\n")
    fs.create_file("/root/A/A1.txt", contents="A1\n")

    runner = CliRunner()
    result = runner.invoke(ascmhl.commands.create, [abspath_conversion_tests("/root"), "-h", "xxh64"])
    assert result.exit_code == 0


@pytest.fixture
@freeze_time("2020-01-15 13:00:00")
def simple_mhl_folder(fs):
    # create a simple folder structure with two files
    fs.create_file("/root/Stuff.txt", contents="stuff\n")
    fs.create_file("/root/A/A1.txt", contents="A1\n")


@pytest.fixture
@freeze_time("2020-01-15 13:00:00")
def post_house_file_structure(fs):
    runner = CliRunner()
    fs.create_file("/root/ShootingDay1/CameraMedia/A/A001/A1.txt", contents="A1")
    fs.create_file("/root/ShootingDay1/CameraMedia/A/A001/A2.txt", contents="A2")
    fs.create_file("/root/ShootingDay1/CameraMedia/A/A001/A3.txt", contents="A3")
    fs.create_file("/root/ShootingDay1/CameraMedia/A/A001/Sidecar.txt", contents="Sidecar1")
    result = runner.invoke(ascmhl.commands.create, [abspath("/root/ShootingDay1/CameraMedia/A"), "-h", "xxh64"])
    assert result.exit_code == 0

    fs.create_file("/root/ShootingDay1/CameraMedia/B/B002/B1.txt", contents="B1")
    fs.create_file("/root/ShootingDay1/CameraMedia/B/B002/B2.txt", contents="B2")
    fs.create_file("/root/ShootingDay1/CameraMedia/B/B002/B3.txt", contents="B3")
    fs.create_file("/root/ShootingDay1/CameraMedia/B/B002/Sidecar.txt", contents="Sidecar2")
    result = runner.invoke(ascmhl.commands.create, [abspath("/root/ShootingDay1/CameraMedia/B"), "-h", "xxh64"])
    assert result.exit_code == 0

    fs.create_file("/root/ShootingDay1/CameraMedia/Report.pdf", contents="A1-3, B1-3")
    result = runner.invoke(ascmhl.commands.create, [abspath("/root/ShootingDay1/CameraMedia"), "-h", "xxh64"])
    assert result.exit_code == 0

    fs.create_file("/root/ShootingDay1/Sound/Takes/Sound.txt", contents="Sound")
    fs.create_file("/root/ShootingDay1/Sound/Sidecar.txt", contents="Sound Sidecar")
    result = runner.invoke(ascmhl.commands.create, [abspath("/root/ShootingDay1/Sound"), "-h", "xxh64"])
    assert result.exit_code == 0

    fs.create_file("/root/ShootingDay1/Report.pdf", contents="A1-3, B1-3, Sound")
    result = runner.invoke(ascmhl.commands.create, [abspath("/root/ShootingDay1"), "-h", "xxh64"])
    assert result.exit_code == 0

    # these are particularly relevant for ignore pattern testing
    fs.create_file("/root/ShootingDay1/CameraMedia/A/Proxy/A001/A1_p.txt", contents="A1 Proxy")
    fs.create_file("/root/ShootingDay1/CameraMedia/A/Proxy/A001/A2_p.txt", contents="A2 Proxy")
    fs.create_file("/root/ShootingDay1/CameraMedia/A/Proxy/A001/A3_p.txt", contents="A3 Proxy")
    fs.create_file("/root/ShootingDay1/CameraMedia/A/Proxy/A001/A001.ale", contents="A001 ALE Proxy")

    fs.create_file("/root/ShootingDay1/CameraMedia/B/Proxy/B001/A1_p.txt", contents="A1 Proxy")
    fs.create_file("/root/ShootingDay1/CameraMedia/B/Proxy/B001/A2_p.txt", contents="A2 Proxy")
    fs.create_file("/root/ShootingDay1/CameraMedia/B/Proxy/B001/A3_p.txt", contents="A3 Proxy")
    fs.create_file("/root/ShootingDay1/CameraMedia/B/Proxy/B001/B001.ale", contents="B001 ALE Proxy")
    fs.create_file("/root/ShootingDay1/CameraMedia/Proxy", contents="Proxy")


@pytest.fixture
@freeze_time("2020-01-15 13:00:00")
def post_house_file_structure_with_range(fs):
    runner = CliRunner()
    for i in range(1, 5):
        for j in range(1, 5):
            fs.create_file(f"/root/ShootingDay1/CameraMedia/A/A00{i}/A00{i}C00{j}.mov", contents=f"A00{i}C00{j}")

    fs.create_file("/root/ShootingDay1/CameraMedia/A/A001/A1.txt", contents="A1")
    fs.create_file("/root/ShootingDay1/CameraMedia/A/A001/A2.txt", contents="A2")
    fs.create_file("/root/ShootingDay1/CameraMedia/A/A001/A3.txt", contents="A3")
    fs.create_file("/root/ShootingDay1/CameraMedia/A/A001/Sidecar.txt", contents="Sidecar1")
    result = runner.invoke(ascmhl.commands.create, [abspath("/root/ShootingDay1/CameraMedia/A"), "-h", "xxh64"])
    assert result.exit_code == 0

    fs.create_file("/root/ShootingDay1/CameraMedia/B/B002/B1.txt", contents="B1")
    fs.create_file("/root/ShootingDay1/CameraMedia/B/B002/B2.txt", contents="B2")
    fs.create_file("/root/ShootingDay1/CameraMedia/B/B002/B3.txt", contents="B3")
    fs.create_file("/root/ShootingDay1/CameraMedia/B/B002/Sidecar.txt", contents="Sidecar2")
    result = runner.invoke(ascmhl.commands.create, [abspath("/root/ShootingDay1/CameraMedia/B"), "-h", "xxh64"])
    assert result.exit_code == 0

    fs.create_file("/root/ShootingDay1/CameraMedia/Report.pdf", contents="A1-3, B1-3")
    result = runner.invoke(ascmhl.commands.create, [abspath("/root/ShootingDay1/CameraMedia"), "-h", "xxh64"])
    assert result.exit_code == 0

    fs.create_file("/root/ShootingDay1/Sound/Takes/Sound.txt", contents="Sound")
    fs.create_file("/root/ShootingDay1/Sound/Sidecar.txt", contents="Sound Sidecar")
    result = runner.invoke(ascmhl.commands.create, [abspath("/root/ShootingDay1/Sound"), "-h", "xxh64"])
    assert result.exit_code == 0

    fs.create_file("/root/ShootingDay1/Report.pdf", contents="A1-3, B1-3, Sound")
    result = runner.invoke(ascmhl.commands.create, [abspath("/root/ShootingDay1"), "-h", "xxh64"])
    assert result.exit_code == 0

    # these are particularly relevant for ignore pattern testing
    fs.create_file("/root/ShootingDay1/CameraMedia/A/Proxy/A001/A1_p.txt", contents="A1 Proxy")
    fs.create_file("/root/ShootingDay1/CameraMedia/A/Proxy/A001/A2_p.txt", contents="A2 Proxy")
    fs.create_file("/root/ShootingDay1/CameraMedia/A/Proxy/A001/A3_p.txt", contents="A3 Proxy")
    fs.create_file("/root/ShootingDay1/CameraMedia/A/Proxy/A001/A001.ale", contents="A001 ALE Proxy")

    fs.create_file("/root/ShootingDay1/CameraMedia/B/Proxy/B001/A1_p.txt", contents="A1 Proxy")
    fs.create_file("/root/ShootingDay1/CameraMedia/B/Proxy/B001/A2_p.txt", contents="A2 Proxy")
    fs.create_file("/root/ShootingDay1/CameraMedia/B/Proxy/B001/A3_p.txt", contents="A3 Proxy")
    fs.create_file("/root/ShootingDay1/CameraMedia/B/Proxy/B001/B001.ale", contents="B001 ALE Proxy")
    fs.create_file("/root/ShootingDay1/CameraMedia/Proxy", contents="Proxy")
