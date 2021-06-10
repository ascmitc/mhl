"""
__author__ = "Jon Waggoner"
__copyright__ = "Copyright 2020, Pomfort GmbH"
__license__ = "MIT"
__maintainer__ = "Patrick Renner, Alexander Sahm"
__email__ = "opensource@pomfort.com"
"""

import os
import pytest
import shutil
from click.testing import CliRunner
from lxml import etree
from testfixtures import TempDirectory
import ascmhl.commands


XML_IGNORE_TAG = "pattern"
XML_HASH_PATH_TAG = "path"

DEFAULT_IGNORE_SET = {".DS_Store", "ascmhl", "ascmhl/"}


@pytest.fixture(scope="function")
def temp_tree():
    """
    fixture used by all tests in this file.
    sets up a static file tree in a temp dir for each test, then deletes after test.
    """
    # create and populate a temp dir with static data
    tmpdir = TempDirectory()
    tmpdir.write("a.txt", b"a")
    tmpdir.write("b.txt", b"b")
    tmpdir.write("1/c.txt", b"c")
    tmpdir.write("1/11/d.txt", b"d")
    tmpdir.write("1/12/e.txt", b"e")
    tmpdir.write("2/11/f.txt", b"f")
    tmpdir.write("2/12/g.txt", b"g")

    # yield the directory to the test function
    yield tmpdir

    # test function is done... cleanup the temp dir
    try:
        tmpdir.cleanup()
    except OSError as e:
        print("Error: %s - %s." % (e.filename, e.strerror))


def ignore_patterns_from_mhl_file(mhl_file: str):
    """
    returns a set of the patterns found in the mhl_file
    """
    pattern_list = [
        element.text for event, element in etree.iterparse(mhl_file) if element.tag.split("}", 1)[-1] == XML_IGNORE_TAG
    ]
    return set(pattern_list)


def paths_from_mhl_file(mhl_file: str):
    """
    returns a set of the hash entires found in the mhl_file
    """
    hash_list = [
        element.text
        for event, element in etree.iterparse(mhl_file)
        if element.tag.split("}", 1)[-1] == XML_HASH_PATH_TAG
    ]
    return set(hash_list)


def assert_mhl_file_has_exact_ignore_patterns(mhl_file: str, patterns_to_check: set):
    """
    asserts the ignore patterns in an mhl are exactly the same as the patterns in patterns_to_check
    this function adds the default ignore spec to the patterns to check since they are always expected
    """
    patterns_in_file = set(ignore_patterns_from_mhl_file(mhl_file))
    assert patterns_in_file == DEFAULT_IGNORE_SET | patterns_to_check, "mhl file has incorrect ignore patterns"


def mhl_file_for_gen(mhl_dir: str, mhl_gen: int):
    """
    returns the mhl file associated with a generation number.
    """
    assert mhl_gen != 0  # ensure we sent the gen number and not array number
    mhl_files = os.listdir(mhl_dir)
    mhl_files.sort()
    return f"{mhl_dir}/{mhl_files[mhl_gen - 1]}"


def test_default_ignore(temp_tree):
    """
    tests that .DS_Store and ascmhl/ fs entries are ignored from the mhl spec
    """
    runner = CliRunner()
    root_dir, mhl_dir = f"{temp_tree.path}", f"{temp_tree.path}/ascmhl"

    # write 2 generations (since ascmhl folder won't exist til after gen 1)
    assert runner.invoke(ascmhl.commands.create, [root_dir]).exit_code == 0
    assert runner.invoke(ascmhl.commands.create, [root_dir]).exit_code == 0

    # ensure we have the expected content in the ascmhl folder
    gen_2_file = mhl_file_for_gen(mhl_dir, 2)
    assert gen_2_file

    gen_2_paths = paths_from_mhl_file(gen_2_file)
    assert "a.txt" in gen_2_paths
    assert "ascmhl" not in gen_2_paths


def test_ignore_on_create(temp_tree):
    """
    tests that the "create" command properly receives and processes all ignore spec arguments
    """
    runner = CliRunner()
    root_dir, mhl_dir = f"{temp_tree.path}", f"{temp_tree.path}/ascmhl"

    # write generation 1,
    runner.invoke(ascmhl.commands.create, [root_dir, "-i", "1"])
    # write generation 2, appending ignore patterns using both CLI args
    runner.invoke(ascmhl.commands.create, [root_dir, "-i", "2", "--ignore", "3"])
    # write generation 3, appending ignore_spec from file and both CLI args
    temp_tree.write("ignorespec", b"6\n7")  # write an ignore spec to file
    runner.invoke(
        ascmhl.commands.create, [root_dir, "-i", "4", "--ignore", "5", "--ignore_spec", f"{temp_tree.path}/ignorespec"]
    )

    # we should now have 3 total mhl generations. ensure each one has exactly the expected patterns
    mhl_files = os.listdir(f"{temp_tree.path}/ascmhl")
    mhl_files.sort()
    assert_mhl_file_has_exact_ignore_patterns(mhl_file_for_gen(mhl_dir, 1), {"1"})
    assert_mhl_file_has_exact_ignore_patterns(mhl_file_for_gen(mhl_dir, 2), {"1", "2", "3"})
    assert_mhl_file_has_exact_ignore_patterns(mhl_file_for_gen(mhl_dir, 3), {"1", "2", "3", "4", "5", "6", "7"})


def test_ignore_on_verify(temp_tree):
    """
    tests that the "verify" command properly receives and processes all ignore spec arguments
    """
    runner = CliRunner()
    root_dir, mhl_dir = f"{temp_tree.path}", f"{temp_tree.path}/ascmhl"

    # create a generation
    runner.invoke(ascmhl.commands.create, [root_dir])
    # purposely alter integrity by deleting a file
    os.remove(f"{root_dir}/a.txt")
    # assert that verification fails
    assert runner.invoke(ascmhl.commands.verify, [root_dir]).exit_code != 0
    # assert that we can suppress this verification error by ignoring the deleted file
    assert runner.invoke(ascmhl.commands.verify, [root_dir, "-i", "a.txt"]).exit_code == 0

    # again, but by ignoring a dir. alter a file, then ignore the parent.
    temp_tree.write(f"{root_dir}/1/c.txt", b"BAD_CONTENTS")
    # assert that verification fails
    assert runner.invoke(ascmhl.commands.verify, [root_dir]).exit_code != 0
    # assert that we can suppress this verification error by ignoring a parent directory
    assert runner.invoke(ascmhl.commands.verify, [root_dir, "-i", "a.txt", "--ignore", "c.txt"]).exit_code == 0

    # assert that the same verification works by using an ignore spec from file
    temp_tree.write("ignorespec", b"a.txt\n1/c.txt")  # write an ignore spec to file
    assert runner.invoke(ascmhl.commands.verify, [root_dir, "--ignore_spec", f"{temp_tree.path}/ignorespec"])


def test_ignore_on_diff(temp_tree):
    """
    tests that the "diff" command properly receives and processes all ignore spec arguments
    """
    runner = CliRunner()
    root_dir, mhl_dir = f"{temp_tree.path}", f"{temp_tree.path}/ascmhl"

    # create a generation
    runner.invoke(ascmhl.commands.create, [root_dir])
    # purposely alter integrity by deleting a file
    os.remove(f"{root_dir}/a.txt")
    # assert that verification fails
    assert runner.invoke(ascmhl.commands.diff, [root_dir]).exit_code != 0
    # assert that we can suppress this verification error by ignoring the deleted file
    assert runner.invoke(ascmhl.commands.diff, [root_dir, "-i", "a.txt"]).exit_code == 0

    # again, but by ignoring a dir. alter a file, then ignore the parent.
    temp_tree.write(f"{root_dir}/1/c.txt", b"BAD_CONTENTS")
    # assert that verification fails
    assert runner.invoke(ascmhl.commands.diff, [root_dir]).exit_code != 0
    # assert that we can suppress this verification error by ignoring a parent directory
    assert runner.invoke(ascmhl.commands.diff, [root_dir, "-i", "a.txt", "--ignore", "1/c.txt"]).exit_code == 0

    # assert that the same verification works by using an ignore spec from file
    temp_tree.write("ignorespec", b"a.txt\n1/c.txt")  # write an ignore spec to file
    assert runner.invoke(ascmhl.commands.diff, [root_dir, "--ignore_spec", f"{temp_tree.path}/ignorespec"])


def test_ignore_on_nested_histories(temp_tree):
    """
    tests that nested histories have proper interaction with the ignore specification.
    parent ignore specs are propagated to their children and appended to the existing child specs.
    ensure we append but do not overwrite.
    """
    runner = CliRunner()
    root_dir, root_mhl_dir = f"{temp_tree.path}", f"{temp_tree.path}/ascmhl"
    child_dir, child_mhl_dir = f"{temp_tree.path}/1", f"{temp_tree.path}/1/ascmhl"

    # create an mhl gen on a nested dir
    runner.invoke(ascmhl.commands.create, [child_dir, "-i", "c1"])
    assert_mhl_file_has_exact_ignore_patterns(mhl_file_for_gen(child_mhl_dir, 1), {"c1"})

    # create mhl gen on parent, ensure parent is correct and child updated.
    runner.invoke(ascmhl.commands.create, [root_dir, "-i", "p1"])
    assert_mhl_file_has_exact_ignore_patterns(mhl_file_for_gen(root_mhl_dir, 1), {"p1"})
    assert_mhl_file_has_exact_ignore_patterns(mhl_file_for_gen(child_mhl_dir, 2), {"c1", "p1"})

    # add just to child again.
    runner.invoke(ascmhl.commands.create, [child_dir, "-i", "c2"])
    assert_mhl_file_has_exact_ignore_patterns(mhl_file_for_gen(child_mhl_dir, 3), {"c1", "p1", "c2"})

    # add to parent and test one last time.
    runner.invoke(ascmhl.commands.create, [root_dir, "-i", "p2"])
    assert_mhl_file_has_exact_ignore_patterns(mhl_file_for_gen(root_mhl_dir, 2), {"p1", "p2"})
    assert_mhl_file_has_exact_ignore_patterns(mhl_file_for_gen(child_mhl_dir, 4), {"c1", "p1", "c2", "p2"})
