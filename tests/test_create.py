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


# TODO: this test should be rewritten as several different tests. Its scope is too broad. This should likely be moved to a hash specific file
@freeze_time("2020-01-16 09:15:00")
def test_create_directory_hashes(fs):
    fs.create_file("/root/Stuff.txt", contents="stuff\n")
    fs.create_file("/root/A/A1.txt", contents="A1\n")

    result = CliRunner().invoke(ascmhl.commands.create, ["/root", "-h", "xxh64", "-v"])
    assert result.exit_code == 0

    # a directory hash for the folder A was created
    hash_list = MHLHistory.load_from_path("/root").hash_lists[0]
    assert hash_list.find_media_hash_for_path("A").is_directory
    assert hash_list.find_media_hash_for_path("A").hash_entries[0].hash_string == "d3904ee76bba3d2a"
    # and the directory hash of the root folder is set in the header
    assert hash_list.process_info.root_media_hash.hash_entries[0].hash_string == "ca56d22f064fdf1b"

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
    assert hash_list.find_media_hash_for_path("A").hash_entries[0].hash_string == "cc195301a14023a9"
    assert hash_list.process_info.root_media_hash.hash_entries[0].hash_string == "4ccac5e6856ecf04"
    # empty folder all have the same directory hash
    assert hash_list.find_media_hash_for_path("emptyFolderA").hash_entries[0].hash_string == "ef46db3751d8e999"
    assert hash_list.find_media_hash_for_path("emptyFolderB").hash_entries[0].hash_string == "ef46db3751d8e999"
    # but since we also contain the file names in the dir hashes an empty folder that contains other empty folders
    # has a different directory structure hash
    assert (
        hash_list.find_media_hash_for_path("emptyFolderC").hash_entries[0].structure_hash_string == "949018e6a4932905"
    )
    # FIXME: emtpyFolderC isn't really empty is it - it has empty dirs inside of it.
    # how do we want to handle empty dirs in empty dirs.
    # the content hash stays the same
    assert hash_list.find_media_hash_for_path("emptyFolderC").hash_entries[0].hash_string == "cf4b060700272aa6"

    # test that the directory-hash command creates the same directory hashes
    # FIXME: command doesn't exist any more, replace with tests of verify directory hashes command?
    #    result = CliRunner().invoke(ascmhl.commands.directory_hash, ["/root"])
    #    assert result.exit_code == 0
    #    assert "  calculated root hash: xxh64: 5f4af3b3fd736415" in result.output

    # altering the content of one file
    with open("/root/A/A2.txt", "a") as file:
        file.write("!!")

    runner = CliRunner()
    result = runner.invoke(ascmhl.commands.create, ["/root", "-v", "-h", "xxh64", "-h", "md5"])
    assert "ERROR: hash mismatch for        A/A2.txt" in result.output
    hash_list = MHLHistory.load_from_path("/root").hash_lists[-1]
    # an altered file leads to a different root directory hash
    assert hash_list.process_info.root_media_hash.hash_entries[1].hash_string == "28ed09733f793dfc"
    # structure hash stays the same
    assert hash_list.process_info.root_media_hash.hash_entries[1].structure_hash_string == "89e4debdb80cc068"

    # test that the directory-hash command creates the same root hash
    # FIXME: command doesn't exist any more, replace with tests of verify directory hashes command?
    #    result = CliRunner().invoke(ascmhl.commands.directory_hash, ["/root"])
    #    assert result.exit_code == 0
    #    assert "root hash: xxh64: adf18c910489663c" in result.output

    assert hash_list.find_media_hash_for_path("B").hash_entries[0].hash_string == "d6df246725efff6ceaee31f663a32cf8"
    assert hash_list.find_media_hash_for_path("B").hash_entries[1].hash_string == "aab0eba57cd1aca9"

    assert (
        hash_list.find_media_hash_for_path("B").hash_entries[0].structure_hash_string
        == "a21e164c1df944733e5e3d4e4ed64f90"
    )
    assert hash_list.find_media_hash_for_path("B").hash_entries[1].structure_hash_string == "fac2a2ceb0fa0c0b"

    assert hash_list.process_info.root_media_hash.hash_entries[1].hash_string == "28ed09733f793dfc"
    assert hash_list.process_info.root_media_hash.hash_entries[1].structure_hash_string == "89e4debdb80cc068"

    # rename one file
    os.rename("/root/B/B1.txt", "/root/B/B2.txt")

    runner = CliRunner()
    result = runner.invoke(ascmhl.commands.create, ["/root", "-v", "-h", "xxh64", "-h", "c4"])
    assert "ERROR: hash mismatch for        A/A2.txt" in result.output
    # in addition to the failing verification we also have a missing file B1/B1.txt
    assert "missing file(s):\n  B/B1.txt" in result.output
    hash_list = MHLHistory.load_from_path("/root").hash_lists[-1]
    # the file name is part of the structure directory hash of the containing directory so it's hash changes
    assert (
        hash_list.find_media_hash_for_path("B").hash_entries[0].structure_hash_string
        == "c42qegPDBxh16Vqi4qFGh1EQv39nEbVmZ9R1LGkaVr1dEBRcD69pH3r5vdGDSwceQLEZc872kQho5Cforb95s2wjH8"
    )
    assert hash_list.find_media_hash_for_path("B").hash_entries[1].structure_hash_string == "7ae620e883160eb3"
    # .. and the content hash stays the same
    assert (
        hash_list.find_media_hash_for_path("B").hash_entries[0].hash_string
        == "c43X1ve8nmicwGit4fnhs428pTCV6ZjXQsorxPLNx3396oRuQFaq79iLR2ZsPoWN8yckFzZdkqZ21igH8K7rWAoDMa"
    )
    assert hash_list.find_media_hash_for_path("B").hash_entries[1].hash_string == "aab0eba57cd1aca9"

    # a renamed file also leads to a different root structure directory hash
    assert hash_list.process_info.root_media_hash.hash_entries[1].structure_hash_string == "0bba67923d19d36b"
    # and an unchanged content hash
    assert hash_list.process_info.root_media_hash.hash_entries[1].hash_string == "28ed09733f793dfc"

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

    # assure that there is a hash entry for the verification of the original hash (hash formats are sorted alphabetically)

    assert media_hash.hash_entries[0].action == "verified"  # formerly 'new'
    assert media_hash.hash_entries[0].hash_format == "md5"

    assert media_hash.hash_entries[1].action == "verified"
    assert media_hash.hash_entries[1].hash_format == "xxh64"


def test_creator_info(fs, simple_mhl_history):
    # test comment
    result = CliRunner().invoke(ascmhl.commands.create, ["/root", "--comment", "a super comment"])
    assert result.exit_code == 0
    result = CliRunner().invoke(ascmhl.commands.info, ["-v", "/root"])
    assert result.exit_code == 0
    assert "a super comment" in result.output

    # test location
    result = CliRunner().invoke(ascmhl.commands.create, ["/root", "--location", "Munich"])
    assert result.exit_code == 0
    result = CliRunner().invoke(ascmhl.commands.info, ["-v", "/root"])
    assert result.exit_code == 0
    assert "Munich" in result.output

    # test author
    result = CliRunner().invoke(
        ascmhl.commands.create,
        [
            "/root",
            "--author_name",
            "Franz",
            "--author_email",
            "franz@example.com",
            "--author_phone",
            "123-4567",
            "--author_role",
            "Data Manager",
        ],
    )
    assert result.exit_code == 0
    result = CliRunner().invoke(ascmhl.commands.info, ["-v", "/root"])
    assert result.exit_code == 0
    assert "Franz" in result.output
    assert "franz@example.com" in result.output
    assert "123-4567" in result.output
    assert "Data Manager" in result.output


def test_create_mulitple_hashformats(fs, simple_mhl_history):
    runner = CliRunner()
    result = runner.invoke(ascmhl.commands.create, ["/root", "-v", "-n", "-h", "md5", "-h", "sha1"])
    assert result.exit_code == 0

    assert "A/A1.txt  md5: fe6975a937016c20b43b17540e6c6246" in result.output
    assert "A/A1.txt  sha1: 4a5b95edbea7de5ed2367432645df88cd4f1d1b6" in result.output


def test_create_mulitple_hashformats_no_dash_n(fs, simple_mhl_history):
    runner = CliRunner()
    result = runner.invoke(ascmhl.commands.create, ["/root", "-v", "-h", "md5", "-h", "sha1"])
    assert result.exit_code == 0

    assert "A/A1.txt  md5: fe6975a937016c20b43b17540e6c6246" in result.output
    assert "A/A1.txt  sha1: 4a5b95edbea7de5ed2367432645df88cd4f1d1b6" in result.output


@freeze_time("2020-01-16 09:15:00")
def test_create_mulitple_hashformats_double_hashformat(fs, simple_mhl_history):
    runner = CliRunner()
    result = runner.invoke(ascmhl.commands.create, ["/root", "-v", "-h", "c4"])
    result = runner.invoke(ascmhl.commands.create, ["/root", "-v", "-h", "md5", "-h", "sha1"])

    # check if mhl file exists
    mhlfilepath = "/root/ascmhl/0003_root_2020-01-16_091500.mhl"
    assert os.path.isfile(mhlfilepath)

    # check if mhl file validates
    result = runner.invoke(ascmhl.commands.xsd_schema_check, [mhlfilepath])
    if result.exit_code != 0:
        print(result.output)

    assert result.exit_code == 0
