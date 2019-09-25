from src.util import pass_context
from src.util import logger
import click


@click.command()
@click.option('-r', '--root', type=click.Path(exists=True, file_okay=False, dir_okay=True, writable=True, readable=True,), help='Specify the directory to verify. Default is current directory.')
@click.option('-q', '--quiet', is_flag=True, help='Disables verbose output of seal verification.')
@pass_context
def verify(ctx, root, quiet):
    ctx.verbose = not quiet
    if root is not None:
        ctx.root = root

    logger.verbose('my verbose log')
    logger.info('my info log')
    logger.error('my error log')
    logger.fatal('my fatal log')
    logger.info('FATAL FAILED!!!!!')