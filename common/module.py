import os
import pkg_resources
from importlib import import_module

INDEX_FILE = 'modindex.txt'


def load_modules(cmds=[]):
    """Read the INDEX_FILE and load all modules.

    Args:
        cmds: list reflecting commands shell supports. only used by server to
              update its internal list
    """

    mods = []

    # a text file named INDEX_FILE is created during the build process that
    # lists the names of all the modules in the modules/ directory. this file
    # is needed because the package has no way to know the names of the modules
    # to load otherwise. it can't use os.listdir('modules') because in
    # production, this is executing in a zip file, so the modules aren't on the
    # filesystem
    for fname in pkg_resources.resource_string(__name__, INDEX_FILE).split():
        if fname.endswith('.py'):
            mod = os.path.splitext(fname)[0]
            if mod == '__init__':
                continue
            elif mod in cmds:
                raise Exception('duplicate module detected')
            mods.append(import_module('modules.' + mod))
            # TODO : validate module structure for required functions
            cmds.append(mod)
            print mod
    return cmds, mods
