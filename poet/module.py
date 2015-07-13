import os
from importlib import import_module


def load_modules(cmds=[]):
    """
    Args:
        cmds: list reflecting commands shell supports. only used by server to
              update its internal list
    """

    mods = []
    for each in os.listdir('modules'):
        if each.endswith('.py'):
            mod = os.path.splitext(each)[0]
            if mod == '__init__':
                continue
            elif mod in cmds:
                raise Exception('duplicate module detected')
            mods.append(import_module('modules.' + mod))
            # TODO : validate module structure for required functions
            cmds.append(mod)
            print mod
    return cmds, mods
