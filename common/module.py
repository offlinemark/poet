import os
import pkg_resources
from importlib import import_module

INDEX_FILE = 'modindex.txt'

client_commands = {}
server_commands = {}


def client_handler(cmd):
    """Decorator to be used by modules for declaring client commands.
    """

    def decorate(func):
        client_commands[cmd] = func
    return decorate


def server_handler(cmd):
    """Decorator to be used by modules for declaring server commands.
    """

    def decorate(func):
        server_commands[cmd] = func
    return decorate


def load_modules():
    """Read the INDEX_FILE and load all modules. Used by client and server.
    """

    # a text file named INDEX_FILE is created during the build process that
    # lists the names of all the modules in the modules/ directory. this file
    # is needed because the package has no way to know the names of the modules
    # to load otherwise. it can't use os.listdir('modules') because in
    # production, this is executing in a zip file, so the modules aren't on the
    # filesystem
    for fname in pkg_resources.resource_string(__name__, INDEX_FILE).split():
        if fname.endswith('.py'):
            mod = os.path.splitext(fname)[0]

            # __init__ isn't a command, but we need it for modules to work
            # correctly
            if mod == '__init__':
                continue
            elif mod in server_commands.keys():
                raise Exception('duplicate module detected: {}'.format(mod))

            import_module('modules.' + mod)
            # TODO : validate module structure for required functions
