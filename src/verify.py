from src.util import pass_context
from src.util import logger
import click


@click.command()
@click.argument('folderpath', type=click.Path(exists=True, file_okay=False, readable=True))
@click.option('--name', '-n', help="Full name of user")
@click.option('--username', '-u', help="Login name of user")
@click.option('--comment', '-c', help="Comment string for human readable context")
@click.option('--hashformat', '-h', type=click.Choice(['xxhash', 'MD5', 'SHA1', 'C4']), multiple=False, default='xxhash')
@click.option('--generationnumber', '-g', help="Generation number to verify against")
@click.option('--simulate', '-s', default=False, is_flag=True, help="Simulate only, don't write new ascmhl file")
@click.option('--directoryhashes', '-d', default=False, is_flag=True, help="Log calculated directory hashes")
@click.option('--write-xattr', '-wx', default=False, is_flag=True, help="Write hashes as xattr to file system")
@click.option('--verbose', '-v', default=False, is_flag=True, help="Verbose output")
@pass_context
def verify(ctx, **kwargs):
    """Verify a folder and create a new ASC-MHL file"""
    ctx.verbose = kwargs.get('verbose')
    ctx.root = kwargs.get('folderpath')

    logger.verbose(f'verifying {ctx.root}')
