from src.util.context import pass_context
import os


@pass_context
def mhl_dir(ctx):
    """absolute path of the asc-mhl folder"""
    return os.path.join(ctx.root, 'asc-mhl')


