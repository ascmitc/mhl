import os
import click


class Context(object):
    def __init__(self):
        self.root = None      # TODO: would we like to default current working directory if the arg isn't provided?
        self.verbose = False  # default not verbose

    def mhl_dir(self):
        return os.path.join(self.root, 'asc-mhl')  # TODO: ensure my folder name is correct


"""
this is a custom decorator that we use instead of the default pass_context that click provides so that our custom context gets injected
"""
pass_context = click.make_pass_decorator(Context, ensure=True)
