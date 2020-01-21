import pytest
import os
import filecmp
import time
from freezegun import freeze_time
from click.testing import CliRunner
from pyfakefs.fake_filesystem_unittest import Pause
from src import verify

scenario_output_path = '../Scenarios/Output'
fake_ref_path = '/ref'


@pytest.fixture(scope="session", autouse=True)
def set_timezone():
    """Fakes the host timezone to UTC so we don't get different mhl files if the tests run on different time zones
    seems like freezegun can't handle timezones like we want"""
    os.environ['TZ'] = 'UTZ'
    time.tzset()


@pytest.fixture()
def reference(fs):
    fs.add_real_directory(scenario_output_path, target_path=fake_ref_path)


@pytest.fixture
@freeze_time("2020-01-15 13:00:00")
def A002R2EC(fs):
    fs.create_file('/A002R2EC/Sidecar.txt', contents='BLOREM ipsum dolor sit amet, consetetur sadipscing elitr.\n')
    fs.create_file('/A002R2EC/Clips/A002C006_141024_R2EC.mov', contents='abcd\n')
    fs.create_file('/A002R2EC/Clips/A002C007_141024_R2EC.mov', contents='def\n')


def compare_file_content(reference, path, fake_fs=None, overwrite_ref=False):
    if os.path.isabs(path):
        relative_path = path.lstrip(os.sep)
    else:
        relative_path = path
    ref_path = os.path.join(fake_ref_path, reference, relative_path)

    if os.path.isfile(path) is True and os.path.isfile(ref_path) is True:
        result = filecmp.cmp(ref_path, path, shallow=False)
    else:
        result = False

    if fake_fs is not None and overwrite_ref is True and result is False and os.path.isfile(path):
        with open(path, 'rb') as src_file:
            data = src_file.read()
            with Pause(fake_fs):
                real_ref_path = os.path.join(scenario_output_path, reference, relative_path)
                with open(real_ref_path, 'w+b') as dst_file:
                    dst_file.write(data)

    return result


@freeze_time("2020-01-16 09:15:00")
def test_scenario_01(fs, reference, A002R2EC):
    """

    """

    # assume the card is copied to a travel drive.

    # create original mhl generation
    runner = CliRunner()
    result = runner.invoke(verify, ['/A002R2EC'])
    assert result.exit_code == 0
    assert compare_file_content('scenario_01', '/A002R2EC/asc-mhl/A002R2EC_2020-01-16_091500_0001.ascmhl', fake_fs=fs, overwrite_ref=True)


@freeze_time("2020-01-16 09:15:00")
def test_scenario_02(fs, reference, A002R2EC):
    """

    """

    # assume the card is copied to a travel drive.

    # create original mhl generation
    runner = CliRunner()
    result = runner.invoke(verify, ['/A002R2EC'])
    assert result.exit_code == 0
    assert compare_file_content('scenario_02', '/A002R2EC/asc-mhl/A002R2EC_2020-01-16_091500_0001.ascmhl', fake_fs=fs, overwrite_ref=True)

    # assume the card is copied from the travel drive to a file server

    with freeze_time("2020-01-17 14:30:00"):
        # create second mhl generation by verifying hashes on the file server
        result = runner.invoke(verify, ['/A002R2EC'])
        assert result.exit_code == 0
        assert compare_file_content('scenario_02', '/A002R2EC/asc-mhl/A002R2EC_2020-01-16_091500_0001.ascmhl')
        assert compare_file_content('scenario_02', '/A002R2EC/asc-mhl/A002R2EC_2020-01-17_143000_0002.ascmhl', fake_fs=fs, overwrite_ref=True)