from src.mhl import pass_context
from src.util import logger
import click


@click.command()
@click.argument('rootpath', type=click.Path(exists=True, file_okay=False, readable=True))
@click.option('--name', '-n', help="Full name of user")
@click.option('--comment', '-c', help="Comment string for human readable context")
@click.option('--hash-format', '-h', type=click.Choice(['xxhash', 'MD5', 'SHA1', 'C4']), multiple=False, default='xxhash')
@click.option('--generation-number', '-g', help="Generation number to verify against")
@click.option('--simulate', '-s', default=False, is_flag=True, help="Simulate only, don't write new ascmhl file")
@click.option('--files-only', '-fo', default=False, is_flag=True, help="Disregard folder hashes and only compute file hashes")
@click.option('--write-xattr', '-wx', default=False, is_flag=True, help="Write hashes as xattr to file system")
@click.option('--verbose', '-v', default=False, is_flag=True, help="Verbose output")
@pass_context
def verify(ctx, **kwargs):
    """Verify a folder and create a new ASC-MHL file"""
    ctx.load_args(**kwargs)
    logger.verbose(f'verifying {ctx.root}')
