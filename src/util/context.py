from src.util import traverse
import os
import click
import getpass


class Context(object):
    """
    Context is a custom object intended to wrap root runtime configurations... most of which are provided upon CLI invocation via arguments.
    """
    def __init__(self):
        self.sys_username = getpass.getuser()
        self.root = None  # TODO: would we like to default current working directory if the arg isn't provided?
        self.name = None
        self.comment = None
        self.hash_format = None
        self.generation_number = None
        self.simulate = None
        self.files_only = None
        self.write_xattr = None
        self.verbose = None

    def load_args(self, **kwargs):
        """
        sets all context properties based on the values contained in the kwargs.
        intended to be called directly with the arguments provided to the cli.
        :param kwargs: all arguments/options from the cli passed along as key word args.
        :return: none
        """
        self.root = kwargs.get('folderpath')
        self.name = kwargs.get('name')
        self.comment = kwargs.get('comment')
        self.hash_format = kwargs.get('hash-format')
        self.generation_number = kwargs.get('generation-number')
        self.simulate = kwargs.get('simulate')
        self.files_only = kwargs.get('files-only')
        self.write_xattr = kwargs.get('write-xattr')
        self.verbose = kwargs.get('verbose')

    @property
    def mhl_dir(self):
        return os.path.join(self.root, 'asc-mhl')

    def traverse_tree(self):
        ignore_prefixes = [self.mhl_dir, '.']
        for tree_node in traverse.post_order_lexicographic(self.root, ignore_prefixes):
            yield tree_node


"""
this is a custom decorator that we use instead of the default pass_context that click provides so that our custom context gets injected.
"""
pass_context = click.make_pass_decorator(Context, ensure=True)
