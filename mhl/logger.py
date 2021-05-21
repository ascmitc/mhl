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
    click.echo(click.style(msg, fg="red", bold=True), file=sys.stderr)


def fatal(msg, *args):
    """Logs a message to stderr, then exits"""
    if args:
        msg %= args
    click.echo(click.style(msg, fg="red", bold=True, blink=True), file=sys.stderr)
    click.get_current_context().abort()
