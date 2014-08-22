#!/usr/bin/env python

import sys
import time
import urllib2
import argparse
import logging as log
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
            else:
                log.info('[!] ({}) Server is inactive'.format(datetime.now()))
            time.sleep(DELAY)
        except KeyboardInterrupt:
            log.info('[-] Perennial terminated.')
            sys.exit(0)

if __name__ == '__main__':
    main()
