import pathspec
from . import logger

default_ignore_list = ['.DS_Store', 'ascmhl']


def spec_from(ignore_filepath=None, ignore_patterns=None):
    """
    combines and de-duplicates entries from an ignore file and an ingore list.
    the ignore file and ignore list will be appended to the default ascmhl ignore patterns.
    if no ignore file or list of ignore patterns are provided, the default patterns will be returned.

    :param ignore_filepath: the directory being iterated
    :param ignore_patterns: an optional list of
    :return: returns the compiled pathspec to be used in ignore path pattern matching
    """
    ignore_list = default_ignore_list

    if ignore_filepath:
        with open(ignore_filepath, 'r') as fh:
            ignore_list.extend(line.rstrip('\n') for line in fh if line is not '\n')

    # while this isn't the most efficient way to deduplicate, i wanted to preserve order.
    if ignore_patterns:
        ignore_list.extend(line for line in ignore_patterns if line not in ignore_list)

    logger.verbose(f'ignore patterns {ignore_list}')
    ignore_spec = pathspec.PathSpec.from_lines('gitwildmatch', iter(ignore_list))
    return ignore_spec
