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
    return [".DS_Store", "ascmhl", "ascmhl/"]


class MHLIgnoreSpec:
    """
    MHLIgnoreSpec wraps the parsing of ignore patterns to create a pathspec.PathSpec instance for filepath matching.
    """

    def __init__(self, existing_pattern_list=None, new_pattern_list=None, new_pattern_file=None):
        self._ignore_list = []
        self.set_patterns(existing_pattern_list, new_pattern_list, new_pattern_file)

    def set_patterns(self, existing_pattern_list=None, new_pattern_list=None, new_pattern_file=None):
        """
        set_patterns will set self.ignore_list to a new empty list then expand it with the supplied params.
        new patterns are applied on top of existing patterns.
        if no existing pattern, the default ignore pattern is used.
        the pattern file is applied on top of the pattern lists.
        no duplicates will be added.
        """
        self._ignore_list = []
        if existing_pattern_list:
            self._append_patterns_list(existing_pattern_list)
        else:
            self._append_patterns_list(default_ignore_list())
        if new_pattern_list:
            self._append_patterns_list(new_pattern_list)
        if new_pattern_file:
            self._append_patterns_from_file(new_pattern_file)

    def get_path_spec(self):
        """
        get_path_spec will return a pathspec.PathSpec instance filled with the contents of self.ignore_list
        the returned pathspec.PathSpec instance can be used to match against filepaths.
        """
        return pathspec.PathSpec.from_lines("gitwildmatch", iter(self._ignore_list))

    def get_pattern_list(self):
        return self._ignore_list.copy()

    def _append_patterns_list(self, patterns_to_append):
        """
        _append_patterns_list extends self.ignore_list with the contents of patterns_to_append.
        duplicates are ignored.
        """
        if patterns_to_append:
            self._ignore_list.extend(line for line in patterns_to_append if line not in self._ignore_list)

    def _append_patterns_from_file(self, filepath):
        """
        _append_patterns_from_file reads each line from a file then sends them to _append_patterns_list()
        """
        patters_from_file = []
        if filepath:
            with open(filepath, "r") as fh:
                patters_from_file.extend(line.rstrip("\n") for line in fh if line != "\n")
                self._append_patterns_list(patters_from_file)

    # For call to repr().
    def __repr__(self):
        return repr(self._ignore_list)

    # For call to str().
    def __str__(self):
        return str(self._ignore_list)
