# template, example module

#
# required
#
import module

#
# your imports
#

# import blah

#
# global vars
#

MODNAME = 'template'
USAGE = """Brief description of module.
usage: template [-h] args go here etc
\noptions:
-h\t\tshow help"""

#
# handlers
#


@module.server_handler(MODNAME)
def server(server, argv):
    """Server handler for module.

    Args:
        server: instance of PoetServer class
        argv: list of arguments entered at server shell
    """

    # your code goes here
    print 'template module, does nothing'
    pass


@module.client_handler(MODNAME)
def client(client, inp):
    """Client handler for module.

    Args:
        client: instance of PoetClient class
        inp: command string sent from server
    """

    # your code goes here
    pass
