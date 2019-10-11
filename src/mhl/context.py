import click


class Context(object):
    """
    Context is a custom object intended to wrap root runtime configurations... most of which are provided upon CLI invocation via options.
    """
    def __init__(self):
        self.sys_username = None
        self.root = None  # TODO: would we like to default to current working directory if the root arg isn't provided?
        self.name = None
        self.comment = None
        self.hash_format = None
        self.generation_number = None
        self.simulate = None
        self.skip_chain_verification = None
        self.directory_hashes = None
        self.write_xattr = None
        self.verbose = None

    def load_args(self, **kwargs):
        """
        sets all context properties based on the values contained in the kwargs.
        intended to be called directly with the arguments and options provided to the cli upon invocation.
        :param kwargs: all arguments/options from the cli passed along as key-word-arguments.
        :return: none
        """
        self.root = kwargs.get('root_path')
        self.name = kwargs.get('name')
        self.comment = kwargs.get('comment')
        self.hash_format = kwargs.get('hash_format')
        self.generation_number = kwargs.get('generation_number')
        self.simulate = kwargs.get('simulate')
        self.skip_chain_verification = kwargs.get('skipchainverification')
        self.directory_hashes = kwargs.get('directory_hashes')
        self.write_xattr = kwargs.get('write_xattr')
        self.verbose = kwargs.get('verbose')


"""
this is a custom decorator that we use instead of the default pass_context that click provides so that our custom context gets injected.
"""
pass_context = click.make_pass_decorator(Context, ensure=True)
