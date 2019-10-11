from src.mhl import pass_context
from src.util import logger
from src.mhl.hash_folder import HashListFolderManager
from src.mhl.chain import Chain
import click



@click.command()
@click.argument('root_path', type=click.Path(exists=True, file_okay=False, readable=True))
@click.option('--generation_number', '-g', required=True, default=1, help="Generation number to check")
@click.option('--chainsignaturepublickey', '-csp', required=True, default=None, help="Path to private key (PEM) file for signing")
@click.option('--verbose', '-v', default=False, is_flag=True, help="Verbose output")
@pass_context
def checksignature(ctx, root_path, generation_number, chainsignaturepublickey, verbose):
    """Verify a signature of an ASC-MHL file
    """

    logger.info(f'checking signature for generation {generation_number}')

    ctx.verbose = verbose
    folder_manager = HashListFolderManager(root_path)
    chain = Chain(folder_manager.ascmhl_chainfile_path())
    generation = chain.generation_with_generation_number(generation_number)

    result = generation.verify_signature(chainsignaturepublickey)

    if result == False:
        # TODO: Patrick: remove info log once _create_README script properly reads stderr output.
        #  this logs to both info and error because the scenarios are not properly setup to read stderr output.
        logger.info(f'ERROR: signature checkfailed')
        logger.error(f'FAILED signature check')
        click.get_current_context().exit(110)

