from os.path import join, isdir
import os


def post_order_lexicographic(top, ignore_paths):
    """
    iterates a file system in the order necessary to generate composite tree hashes.

    :param top: the directory being iterated
    :param ignore_paths: paths included in ignore_paths will not be yielded to the caller
    :return: yields results in the order necessary for composite directory hashes
    """
    # create a sorted list of our immediate children
    names = os.listdir(top)
    names.sort()

    # list of tuples. each tuple contains the child name and whether the child is a directory.
    children = []
    for name in names:
        path = join(top, name)
        if path in ignore_paths:
            continue
        children.append((name, isdir(path)))

    # if directory, yield children recursively in post order until exhausted.
    for name, is_dir in children:
        if is_dir:
            path = join(top, name)
            if not os.path.islink(path):
                for x in post_order_lexicographic(path, ignore_paths):
                    yield x

    # now that all children have been traversed, yield the top (current) directory and all of it's sorted children.
    yield top, children
