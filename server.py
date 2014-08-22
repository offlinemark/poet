#!/usr/bin/env python

import socket
import argparse
from datetime import datetime

SIZE = 1024


def get_args():
    """ Parse arguments and return dictionary. """

    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--port')
    return parser.parse_args()


def client_init(ping):
    if ping.startswith('GET /style.css HTTP/1.1'):
        return True
    else:
        return False


def main():
    args = get_args()
    PORT = int(args.port) if args.port else 443

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('', PORT))
    s.listen(1)
    print '[+] Perennial server started on {}.'.format(PORT)

    while True:
        conn, addr = s.accept()
        print '[i] Connected By: {} at {}'.format(addr, datetime.now())
        ping = conn.recv(SIZE)
        if client_init(ping):
            with open('fakeOK.txt') as ok:
                conn.send(ok.read())
        conn.close()

if __name__ == '__main__':
    main()
