"""
__author__ = "Alexander Sahm"
__copyright__ = "Copyright 2020, Pomfort GmbH"

__license__ = "MIT"
__maintainer__ = "Patrick Renner, Alexander Sahm"
__email__ = "opensource@pomfort.com"
"""

from os.path import join, isdir
import os

from . import logger


def post_order_lexicographic(top, ignore_spec):
    """
    iterates a file system in the order necessary to generate composite tree hashes, bypassing ignored paths.

    :param top: the directory being iterated
    :param ignore_spec: the pathspec of ignore patterns to match file exclusions against
    :return: yields results in folder chunks, in the order necessary for composite directory hashes
    """
    # create a sorted list of our immediate children
    names = os.listdir(top)
    names.sort()

    # list of tuples. each tuple contains the child name and whether the child is a directory.
    children = []
    for name in names:
        file_path = os.path.join(top, name)
        if ignore_spec and ignore_spec.match_file(file_path):
            logger.verbose(f'ignoring filepath {file_path}')
            continue
        path = join(top, name)
        children.append((name, isdir(path)))

    # if directory, yield children recursively in post order until exhausted.
    for name, is_dir in children:
        if is_dir:
            path = join(top, name)
            if not os.path.islink(path):
                for x in post_order_lexicographic(path, ignore_spec):
                    yield x

    # now that all children have been traversed, yield the top (current) directory and all of it's sorted children.
    yield top, children
