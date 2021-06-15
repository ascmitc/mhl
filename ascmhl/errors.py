"""
__author__ = "Jon Waggoner, Patrick Renner"
__copyright__ = "Copyright 2020, Pomfort GmbH"

__license__ = "MIT"
__maintainer__ = "Patrick Renner"
__email__ = "opensource@pomfort.com"
"""

import click


class CompletenessCheckFailedException(click.ClickException):
    exit_code = 15

    def __init__(self):
        super().__init__("Files referenced in the ASC MHL history are missing")


class NoMHLHistoryException(click.ClickException):
    exit_code = 11

    def __init__(self, path):
        super().__init__(f"Missing ASC MHL history at path {path}")


class VerificationFailedException(click.ClickException):
    exit_code = 12

    def __init__(self):
        super().__init__("Verification of files referenced in the ASC MHL history failed")


class VerificationDirectoriesFailedException(click.ClickException):
    exit_code = 15

    def __init__(self):
        super().__init__("Verification of directories referenced in the ASC MHL history failed")


class NewFilesFoundException(click.ClickException):
    exit_code = 13

    def __init__(self):
        super().__init__("New files not referenced in the ASC MHL history have been found")


class NoMHLHistoryExceptionForPath(click.ClickException):
    exit_code = 14

    def __init__(self, path):
        super().__init__(f"Missing ASC MHL history for path {path}")
