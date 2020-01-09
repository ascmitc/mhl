from os.path import join, isdir
import os


# TODO: implement this on next refactor. this is not yet integrated into mhl script.
#  iteration logic should not be in the same place as the thing using the iterator when it is this complicated.
#  therefor we should use this generator to easily separate the traversal from the hash computation and xml building
def post_order_lexicographic(top, ignore_file_names):
    """
    iterates a file system in the order necessary to generate composite tree hashes.

    :param top: the directory being iterated
    :param ignore_file_names: file names included in ignore_file_names will not be yielded to the caller
    :return: yields results in folder chunks, in the order necessary for composite directory hashes
    """
    # create a sorted list of our immediate children
    names = os.listdir(top)
    names.sort()

    # list of tuples. each tuple contains the child name and whether the child is a directory.
    children = []
    for name in names:
        if name in ignore_file_names:
            continue
        path = join(top, name)
        children.append((name, isdir(path)))

    # if directory, yield children recursively in post order until exhausted.
    for name, is_dir in children:
        if is_dir:
            path = join(top, name)
            if not os.path.islink(path):
                for x in post_order_lexicographic(path, ignore_file_names):
                    yield x

    # now that all children have been traversed, yield the top (current) directory and all of it's sorted children.
    yield top, children
