import module

MODNAME = 'chint'
USAGE = """Print or change client delay interval.
usage: chint [-h] [seconds]
\nIf run with no arguments, print the current client delay.
Otherwise, change interval to given argument (seconds).
Minimum allowed value is 1.
\noptions:
-h\t\tshow help"""


@module.server_handler(MODNAME)
def server(server, argv):
    if '-h' in argv or '--help' in argv:
        print USAGE
        return

    if len(argv) > 1:
        # argument was given
        try:
            num = int(argv[1])
        except ValueError:
            print USAGE
            return
        if num < 1:
            server.info('Invalid interval time')
        else:
            resp = server.conn.exchange(' '.join(argv))
            msg = 'successful' if resp == 'done' else 'error: ' + resp
            server.info('chint ({}) {}'.format(num, msg))
    else:
        # no argument
        print server.conn.exchange(argv[0])


@module.client_handler(MODNAME)
def client(client, inp):
    if inp == 'chint':
        # no arg, so just send back the interval
        client.s.send(str(client.get_args_interval()))
    else:
        # set interval to arg
        num = int(inp.split()[1])
        if num < 1:
            msg = 'Invalid interval time.'
        else:
            client.set_args_interval(num)
            msg = 'done'
        client.s.send(msg)
