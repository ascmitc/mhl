"""
__author__ = "Jon Waggoner, Patrick Renner"
__copyright__ = "Copyright 2020, Pomfort GmbH"

__license__ = "MIT"
__maintainer__ = "Patrick Renner"
__email__ = "opensource@pomfort.com"
"""

import click


class CompletenessCheckFailedException(click.ClickException):
    exit_code = 10

    def __init__(self):
        super().__init__("Files referenced in the ASC MHL history are missing")


class VerificationFailedException(click.ClickException):
    exit_code = 11

    def __init__(self):
        super().__init__("Verification of files referenced in the ASC MHL history failed")


class VerificationDirectoriesFailedException(click.ClickException):
    exit_code = 12

    def __init__(self):
        super().__init__("Verification of directories referenced in the ASC MHL history failed")


class SingleFileNotFoundException(click.ClickException):
    exit_code = 20

    def __init__(self):
        super().__init__("Could not find single file.")


class NewFilesFoundException(click.ClickException):
    exit_code = 21

    def __init__(self):
        super().__init__("New files not referenced in the ASC MHL history have been found")


class NoMHLHistoryException(click.ClickException):
    exit_code = 30

    def __init__(self, path):
        super().__init__(f"Missing ASC MHL history at path {path}")


class ModifiedMHLManifestFileException(click.ClickException):
    exit_code = 31

    def __init__(self, path):
        super().__init__(f"Modified ASC MHL manifest in history at path {path}")


class NoMHLChainException(click.ClickException):
    exit_code = 32

    def __init__(self, path):
        super().__init__(f"Missing ASC MHL chain file for path {path}")


class MissingMHLManifestException(click.ClickException):
    exit_code = 33

    def __init__(self, path):
        super().__init__(f"Missing ASC MHL manifest in history at path {path}")
