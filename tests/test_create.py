"""
__author__ = "Alexander Sahm"
__copyright__ = "Copyright 2020, Pomfort GmbH"

__license__ = "MIT"
__maintainer__ = "Patrick Renner, Alexander Sahm"
__email__ = "opensource@pomfort.com"
"""

import os
from freezegun import freeze_time
from click.testing import CliRunner

from ascmhl.history import MHLHistory
import ascmhl.commands

scenario_output_path = "examples/scenarios/Output"
fake_ref_path = "/ref"


@freeze_time("2020-01-16 09:15:00")
def test_create_succeed(fs):
    fs.create_file("/root/Stuff.txt", contents="stuff\n")
    fs.create_file("/root/A/A1.txt", contents="A1\n")

    runner = CliRunner()
    result = runner.invoke(ascmhl.commands.create, ["/root", "-h", "xxh64", "-v"])
    assert not result.exception
    assert os.path.exists("/root/ascmhl/0001_root_2020-01-16_091500.mhl")
    # with open('/root/ascmhl/0001_root_2020-01-16_091500.mhl', 'r') as fin:
    #     print(fin.read())
    assert os.path.exists("/root/ascmhl/ascmhl_chain.xml")


@freeze_time("2020-01-16 09:15:00")
def test_create_directory_hashes(fs):
    fs.create_file("/root/Stuff.txt", contents="stuff\n")
    fs.create_file("/root/A/A1.txt", contents="A1\n")

    result = CliRunner().invoke(ascmhl.commands.create, ["/root", "-h", "xxh64", "-v"])
    assert result.exit_code == 0

    # a directory hash for the folder A was created
    hash_list = MHLHistory.load_from_path("/root").hash_lists[0]
    assert hash_list.find_media_hash_for_path("A").is_directory
    assert hash_list.find_media_hash_for_path("A").hash_entries[0].hash_string == "95e230e90be29dd6"
    # and the directory hash of the root folder is set in the header
    assert hash_list.process_info.root_media_hash.hash_entries[0].hash_string == "36e824bc313f3b77"

    # test that the directory-hash command creates the same directory hashes
    # FIXME: command doesn't exist any more, replace with tests of verify directory hashes command?
    #    result = CliRunner().invoke(ascmhl.commands.directory_hash, ["/root", "-v"])
    #    assert result.exit_code == 0
    #    assert "directory hash for: /root/A xxh64: ee2c3b94b6eecb8d" in result.output
    #    assert "root hash: xxh64: 15ef0ade91fff267" in result.output

    # add some more files and folders
    fs.create_file("/root/B/B1.txt", contents="B1\n")
    fs.create_file("/root/A/A2.txt", contents="A2\n")
    fs.create_file("/root/A/AA/AA1.txt", contents="AA1\n")
    os.mkdir("/root/emptyFolderA")
    os.mkdir("/root/emptyFolderB")
    os.mkdir("/root/emptyFolderC")
    os.mkdir("/root/emptyFolderC/emptyFolderCA")
    os.mkdir("/root/emptyFolderC/emptyFolderCB")

    runner = CliRunner()
    result = runner.invoke(ascmhl.commands.create, ["/root", "-v", "-h", "xxh64"])
    assert result.exit_code == 0

    hash_list = MHLHistory.load_from_path("/root").hash_lists[-1]
    # due to the additional content the directory hash of folder A and the root folder changed
    assert hash_list.find_media_hash_for_path("A").hash_entries[0].hash_string == "a8d0ad812ab102bd"
    assert hash_list.process_info.root_media_hash.hash_entries[0].hash_string == "d6b881fed0b325bd"
    # empty folder all have the same directory hash
    assert hash_list.find_media_hash_for_path("emptyFolderA").hash_entries[0].hash_string == "ef46db3751d8e999"
    assert hash_list.find_media_hash_for_path("emptyFolderB").hash_entries[0].hash_string == "ef46db3751d8e999"
    # but since we also contain the file names in the dir hashes an empty folder that contains other empty folders
    # has a different directory structure hash
    assert (
        hash_list.find_media_hash_for_path("emptyFolderC").hash_entries[0].structure_hash_string == "a5e6b8f95dfe2762"
    )
    # the content hash stays the same
    assert hash_list.find_media_hash_for_path("emptyFolderC").hash_entries[0].hash_string == "ef46db3751d8e999"

    # test that the directory-hash command creates the same directory hashes
    # FIXME: command doesn't exist any more, replace with tests of verify directory hashes command?
    #    result = CliRunner().invoke(ascmhl.commands.directory_hash, ["/root"])
    #    assert result.exit_code == 0
    #    assert "  calculated root hash: xxh64: 5f4af3b3fd736415" in result.output

    # altering the content of one file
    with open("/root/A/A2.txt", "a") as file:
        file.write("!!")

    runner = CliRunner()
    result = runner.invoke(ascmhl.commands.create, ["/root", "-v", "-h", "xxh64"])
    assert "ERROR: hash mismatch for        A/A2.txt" in result.output
    hash_list = MHLHistory.load_from_path("/root").hash_lists[-1]
    # an altered file leads to a different root directory hash
    assert hash_list.process_info.root_media_hash.hash_entries[0].hash_string == "cae6659fc7b34c2f"
    # structure hash stays the same
    assert hash_list.process_info.root_media_hash.hash_entries[0].structure_hash_string == "2c99e94e8fa7d90c"

    # test that the directory-hash command creates the same root hash
    # FIXME: command doesn't exist any more, replace with tests of verify directory hashes command?
    #    result = CliRunner().invoke(ascmhl.commands.directory_hash, ["/root"])
    #    assert result.exit_code == 0
    #    assert "root hash: xxh64: adf18c910489663c" in result.output

    assert hash_list.find_media_hash_for_path("B").hash_entries[0].hash_string == "51fb8fb099e92821"
    assert hash_list.find_media_hash_for_path("B").hash_entries[0].structure_hash_string == "945ecf443295ffbd"
    assert hash_list.process_info.root_media_hash.hash_entries[0].hash_string == "cae6659fc7b34c2f"
    assert hash_list.process_info.root_media_hash.hash_entries[0].structure_hash_string == "2c99e94e8fa7d90c"

    # rename one file
    os.rename("/root/B/B1.txt", "/root/B/B2.txt")

    runner = CliRunner()
    result = runner.invoke(ascmhl.commands.create, ["/root", "-v", "-h", "xxh64"])
    assert "ERROR: hash mismatch for        A/A2.txt" in result.output
    # in addition to the failing verification we also have a missing file B1/B1.txt
    assert "missing file(s):\n  B/B1.txt" in result.output
    hash_list = MHLHistory.load_from_path("/root").hash_lists[-1]
    # the file name is part of the structure directory hash of the containing directory so it's hash changes
    assert hash_list.find_media_hash_for_path("B").hash_entries[0].structure_hash_string == "fa4e99472911e118"
    # .. and the content hash stays the same
    assert hash_list.find_media_hash_for_path("B").hash_entries[0].hash_string == "51fb8fb099e92821"

    # a renamed file also leads to a different root structure directory hash
    assert hash_list.process_info.root_media_hash.hash_entries[0].structure_hash_string == "b758c9b165fb6c2a"
    # and an unchanged content hash
    assert hash_list.process_info.root_media_hash.hash_entries[0].hash_string == "cae6659fc7b34c2f"

    # test that the directory-hash command creates the same root hash
    # FIXME: command doesn't exist any more, replace with tests of verify directory hashes command?


#    result = CliRunner().invoke(ascmhl.commands.directory_hash, ["/root"])
#    assert result.exit_code == 0
#    assert "root hash: xxh64: 01441cdf1803e2b8" in result.output


@freeze_time("2020-01-16 09:15:00")
def test_create_no_directory_hashes(fs):
    fs.create_file("/root/Stuff.txt", contents="stuff\n")
    fs.create_file("/root/A/A1.txt", contents="A1\n")
    os.mkdir("/root/emptyFolder")

    runner = CliRunner()
    result = runner.invoke(ascmhl.commands.create, ["/root", "-v", "-n"])
    assert result.exit_code == 0

    # a directory entry without hash was created for the folder A
    hash_list = MHLHistory.load_from_path("/root").hash_lists[0]
    assert hash_list.find_media_hash_for_path("A").is_directory
    assert len(hash_list.find_media_hash_for_path("A").hash_entries) == 0
    # and no directory hash of the root folder is set in the header
    assert len(hash_list.process_info.root_media_hash.hash_entries) == 0
    # the empty folder is still referenced even if not creating directory hashes
    assert hash_list.find_media_hash_for_path("emptyFolder").is_directory

    # removing an empty folder will cause creating a new generation to fail
    os.removedirs("/root/emptyFolder")
    runner = CliRunner()
    result = runner.invoke(ascmhl.commands.create, ["/root", "-v", "-n"])
    assert result.exit_code == 15
    assert "1 missing file(s):\n  emptyFolder" in result.output


def test_create_fail_altered_file(fs, simple_mhl_history):
    # alter a file
    with open("/root/Stuff.txt", "a") as file:
        file.write("!!")

    result = CliRunner().invoke(ascmhl.commands.create, ["/root"])
    assert result.exit_code == 12
    assert "Stuff.txt" in result.output

    # since the file is still altered every other seal will fail as well since we compare to the original hash
    result = CliRunner().invoke(ascmhl.commands.create, ["/root"])
    assert result.exit_code == 12
    assert "Stuff.txt" in result.output

    # when we now choose a new hash format we still fail but will add the new hash in the new format
    result = CliRunner().invoke(ascmhl.commands.create, ["/root", "-h", "md5"])
    assert result.exit_code == 12
    assert "Stuff.txt" in result.output

    root_history = MHLHistory.load_from_path("/root")
    stuff_txt_latest_media_hash = root_history.hash_lists[-1].find_media_hash_for_path("Stuff.txt")
    # the media hash for the Stuff.txt in the latest generation contains the failed xxh64 hash of the altered file
    assert stuff_txt_latest_media_hash.hash_entries[0].hash_format == "xxh64"
    assert stuff_txt_latest_media_hash.hash_entries[0].hash_string == "2346e97eb08788cc"
    assert stuff_txt_latest_media_hash.hash_entries[0].action == "failed"
    # and it contains NO new md5 hash value of the altered file
    assert len(stuff_txt_latest_media_hash.hash_entries) == 1

    # since we didn't add a new md5 hash for the failing file before creating a new generation will still fail for the altered file
    result = CliRunner().invoke(ascmhl.commands.create, ["/root", "-h", "md5"])
    assert result.exit_code == 12
    assert "Stuff.txt" in result.output


def test_create_fail_missing_file(fs, nested_mhl_histories):
    """
    test that creating a new generation fails if there is a file missing on the file system that is referenced by one of the histories
    """

    root_history = MHLHistory.load_from_path("/root")
    paths = root_history.set_of_file_paths()

    assert paths == {"/root/B/B1.txt", "/root/B/BB/BB1.txt", "/root/Stuff.txt", "/root/A/AA/AA1.txt"}
    os.remove("/root/A/AA/AA1.txt")
    runner = CliRunner()
    result = runner.invoke(ascmhl.commands.create, ["/root"])
    assert result.exit_code == 15
    assert "1 missing file(s):\n  A/AA/AA1.txt" in result.output

    # the actual seal has been written to disk anyways we expect the history to contain
    # the new not yet referenced files (/root/B/BA/BA1.txt and /root/A/AB/AB1.txt) as well now
    root_history = MHLHistory.load_from_path("/root")
    paths = root_history.set_of_file_paths()

    # since we scan all generations for file paths we now get old files, missing files and new files here
    # as well as all entries for the directories
    assert paths == {
        "/root/B/B1.txt",
        "/root/B/BA/BA1.txt",
        "/root/B",
        "/root/A/AA",
        "/root/A/AB/AB1.txt",
        "/root/B/BA",
        "/root/A/AA/AA1.txt",
        "/root/A/AB",
        "/root/Stuff.txt",
        "/root/B/BB",
        "/root/A",
        "/root/B/BB/BB1.txt",
    }

    # since the file /root/A/AA/AA1.txt is still missing all further seal attempts will still fail
    runner = CliRunner()
    result = runner.invoke(ascmhl.commands.create, ["/root"])
    assert result.exit_code == 15
    assert "1 missing file(s):\n  A/AA/AA1.txt" in result.output


def test_create_nested_new_format(fs, nested_mhl_histories):
    """
    test that ensures that hasehs in a new format are also verified in child histories
    used to verify fix of bug: https://github.com/ascmitc/mhl/issues/48
    """

    runner = CliRunner()
    result = runner.invoke(ascmhl.commands.create, ["/root", "-h", "md5"])
    assert result.exit_code == 0

    # load one of the the nested histories and check the first media hash of the last generation
    nested_history = MHLHistory.load_from_path("/root/A/AA")
    media_hash = nested_history.hash_lists[-1].media_hashes[0]

    # assure that the first hash entry is the verification of the original hash
    assert media_hash.hash_entries[0].action == "verified"
    assert media_hash.hash_entries[0].hash_format == "xxh64"

    # assure that the second hash entry is the new md5 hash
    assert media_hash.hash_entries[1].action == "verified"  # formerly 'new'
    assert media_hash.hash_entries[1].hash_format == "md5"
