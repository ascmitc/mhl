"""
__author__ = "Jon Waggoner"
__copyright__ = "Copyright 2020, Pomfort GmbH"

__license__ = "MIT"
__maintainer__ = "Jon Waggoner"
__email__ = "opensource@jonwaggoner.com"
"""

from os.path import join, isdir
import os

from . import logger
import pathspec
from .__version__ import ascmhl_folder_name


def post_order_lexicographic(top: str, ignore_pathspec: pathspec.PathSpec = None):
    """
    iterates a file system in the order necessary to generate composite tree hashes, bypassing ignored paths.

    :param top: the directory being iterated
    :param ignore_pathspec: the pathspec of ignore patterns to match file exclusions against
    :return: yields results in folder chunks, in the order necessary for composite directory hashes
    """
    # create a sorted list of our immediate children
    names = os.listdir(top)
    names.sort()

    # list of tuples. each tuple contains the child name and whether the child is a directory.
    children = []
    for name in names:
        file_path = os.path.join(top, name)
        if ignore_pathspec and ignore_pathspec.match_file(file_path):
            if os.path.basename(os.path.normpath(file_path)) != ascmhl_folder_name:
                logger.verbose(f"ignoring filepath {file_path}")
            continue
        path = join(top, name)
        children.append((name, isdir(path)))

    # if directory, yield children recursively in post order until exhausted.
    for name, is_dir in children:
        if is_dir:
            path = join(top, name)
            if not os.path.islink(path):
                for x in post_order_lexicographic(path, ignore_pathspec):
                    yield x

    # now that all children have been traversed, yield the top (current) directory and all of it's sorted children.
    yield top, children
