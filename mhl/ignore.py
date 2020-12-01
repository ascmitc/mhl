"""
__author__ = "Jon Waggoner"
__copyright__ = "Copyright 2020, Pomfort GmbH"

__license__ = "MIT"
__maintainer__ = "Jon Waggoner"
__email__ = "opensource@jonwaggoner.com"
"""

import pathspec
from . import logger


def default_ignore_list():
    return ['.DS_Store', 'ascmhl']


class IgnoreSpec:
    """
    class to wrap ignore spec creation
    intended use: set the patterns then get a pathspec.PathSpec instance.
    """

    def __init__(self):
        self.ignore_list = default_ignore_list()

    def set_patterns(self, existing_pattern_list=None, new_pattern_list=None, new_pattern_file=None):
        """
        set_patterns will set self.ignore_list to a new empty list then expand it with the supplied params.
        if no existing pattern, this will use default.
        new patterns are applied on top of existing patterns.
        the pattern file is applied on top of the pattern lists.
        no duplicates will be added.
        """
        self.ignore_list = []
        if existing_pattern_list:
            self._append_patterns_list(existing_pattern_list)
        else:
            self._append_patterns_list(default_ignore_list())
        if new_pattern_list:
            self._append_patterns_list(new_pattern_list)
        if new_pattern_file:
            self._append_patterns_from_file(new_pattern_file)
        logger.verbose("set ignore patterns")

    def get_path_spec(self):
        """
        get_path_spec will return a pathspec.PathSpec instance filled with the contents of self.ignore_list
        the returned pathspec.PathSpec instance can be used to match against filepaths.
        """
        return pathspec.PathSpec.from_lines('gitwildmatch', iter(self.ignore_list))

    def _append_patterns_list(self, patterns_to_append):
        """
        _append_patterns_list extends self.ignore_list with the contents of patterns_to_append.
        duplicates are ignored.
        """
        if patterns_to_append:
            self.ignore_list.extend(line for line in patterns_to_append if line not in self.ignore_list)

    def _append_patterns_from_file(self, filepath):
        """
        _append_patterns_from_file reads each line from a file then sends them to _append_patterns_list()
        """
        patters_from_file = []
        if filepath:
            with open(filepath, 'r') as fh:
                patters_from_file.extend(line.rstrip('\n') for line in fh if line is not '\n')
                self._append_patterns_list(patters_from_file)


def spec_from(ignore_filepath=None, ignore_patterns=None):
    """
    combines and de-duplicates entries from an ignore file and an ingore list.
    the ignore file and ignore list will be appended to the default ascmhl ignore patterns.
    if no ignore file or list of ignore patterns are provided, the default patterns will be returned.

    :param ignore_filepath: the directory being iterated
    :param ignore_patterns: an optional list of
    :return: returns the compiled pathspec to be used in ignore path pattern matching
    """
    ignore_list = default_ignore_list()

    if ignore_filepath:
        with open(ignore_filepath, 'r') as fh:
            ignore_list.extend(line.rstrip('\n') for line in fh if line not in ignore_list)

    if ignore_patterns:
        ignore_list.extend(line for line in ignore_patterns if line not in ignore_list)

    logger.verbose(f'ignore patterns {ignore_list}')
    ignore_spec = pathspec.PathSpec.from_lines('gitwildmatch', iter(ignore_list))
    return ignore_spec
