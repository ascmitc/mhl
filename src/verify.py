from src.mhl import pass_context
from src.util import logger
from src.mhl.hash_folder import HashListFolderManager
from src.mhl.hash_list import HashListCreator, HashListReader
import click
import os


@click.command()
@click.argument('root_path', type=click.Path(exists=True, file_okay=False, readable=True))
@click.option('--name', '-n', help="Full name of user")
@click.option('--comment', '-c', help="Comment string for human readable context")
@click.option('--hash_format', '-h', type=click.Choice(['xxhash', 'MD5', 'SHA1', 'C4']), multiple=False, default='xxhash')
@click.option('--generation_number', '-g', default=0, help="Generation number to verify against")
@click.option('--simulate', '-s', default=False, is_flag=True, help="Simulate only, don't write new ascmhl file")
@click.option('--files_only', '-fo', default=False, is_flag=True, help="Disregard folder hashes and only compute file hashes")
@click.option('--write_xattr', '-wx', default=False, is_flag=True, help="Write hashes as xattr to file system")
@click.option('--verbose', '-v', default=False, is_flag=True, help="Verbose output")
@pass_context
def verify(ctx, **kwargs):
    """Verify a folder and create a new ASC-MHL file"""
    ctx.load_args(**kwargs)
    logger.verbose(f'verifying {ctx.root}')

    folder_manager = HashListFolderManager(ctx.root)
    if ctx.generation_number is None:
        ctx.generation_number = folder_manager.earliest_ascmhl_generation_number()

    # TODO: functions like "path_for_ascmhl_generation_number" can be global functions and can ask the context for the data needed.
    ascmhl_path = folder_manager.path_for_ascmhl_generation_number(ctx.generation_number)
    if ctx.generation_number and ascmhl_path is None:
        logger.fatal(f'no matching mhl file for generation number {ctx.generation_number}')

    # TODO: anything that needs this "info" type of data should be refactored to just grab it from the context. out of time.
    creator = HashListCreator(ctx.root, {
        'username': ctx.sys_username,
        'name': ctx.name,
        'comment': ctx.comment
    })
    creator.create_directory_hashes = not ctx.files_only
    creator.write_xattr = ctx.write_xattr
    creator.simulate = ctx.simulate

    if ascmhl_path is not None:
        reader = HashListReader(ascmhl_path, ctx.generation_number)
        reader.parse()

        number_failures = creator.traverse_with_existing_hashes(reader.media_hash_list, ctx.hash_format)
        if number_failures > 0:
            logger.error(f'FAILED verification for {number_failures} file(s)')
        if not ctx.simulate:
            folder_manager.write_ascmhl(creator.xml_string())
    else:
        creator.traverse(ctx.hash_format)
        if not ctx.simulate:
            if not os.path.exists(folder_manager.ascmhl_folder_path()):
                os.makedirs(folder_manager.ascmhl_folder_path())
            folder_manager.write_ascmhl(creator.xml_string())
