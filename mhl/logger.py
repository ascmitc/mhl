"""
__author__ = "Jon Waggoner, Patrick Renner"
__copyright__ = "Copyright 2020, Pomfort GmbH"

__license__ = "MIT"
__maintainer__ = "Patrick Renner"
__email__ = "opensource@pomfort.com"
"""

import sys
import click

verbose_logging = False
debug_logging = False


def debug(msg, *args):
    """Logs a message to stdout only if debug is enabled."""
    if debug_logging:
        info(msg, *args)


def verbose(msg, *args):
    """Logs a message to stdout only if verbose is enabled."""
    if verbose_logging:
        info(msg, *args)


def info(msg, *args):
    """Logs a message to stdout."""
    if args:
        msg %= args
    click.echo(msg, file=sys.stdout)


def error(msg, *args):
    """Logs a message to stderr"""
    if args:
        msg %= args
    click.echo(click.style(msg, fg='red', bold=True), file=sys.stderr)


def fatal(msg, *args):
    """Logs a message to stderr, then exits"""
    if args:
        msg %= args
    click.echo(click.style(msg, fg='red', bold=True, blink=True), file=sys.stderr)
    click.get_current_context().abort()


class CompletenessCheckFailedException(click.ClickException):
    exit_code = 15

    def __init__(self):
        super().__init__('Files referenced in the mhl history are missing')


class NoMHLHistoryException(click.ClickException):
    exit_code = 11

    def __init__(self, path):
        super().__init__(f'Missing mhl history at path {path}')


class VerificationFailedException(click.ClickException):
    exit_code = 12

    def __init__(self):
        super().__init__('Verification of files referenced in the mhl history failed')


class NewFilesFoundException(click.ClickException):
    exit_code = 13

    def __init__(self):
        super().__init__('New files not referenced in the mhl history have been found')
