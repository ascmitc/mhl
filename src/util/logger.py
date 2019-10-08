from src.mhl import pass_context
import sys
import click


@pass_context
def verbose(ctx, msg, *args):
    """Logs a message to stdout only if verbose is enabled."""
    if ctx.verbose:
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
