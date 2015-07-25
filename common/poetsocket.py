import base64
import struct
import socket

SIZE = 4096
PREFIX_LEN = 4


class PoetSocket(object):
    """Socket wrapper for client/server communications.

    Attributes:
        s: socket instance

    Socket abstraction which uses the convention that the message is prefixed
    by a big-endian 32 bit value indicating the length of the following base64
    string.
    """

    def __init__(self, s):
        self.s = s

    def close(self):
        self.s.close()

    def exchange(self, msg):
        self.send(msg)
        return self.recv()

    def send(self, msg):
        """Send message over socket."""

        pkg = base64.b64encode(msg)
        pkg_size = struct.pack('>I', len(pkg))
        sent = self.s.sendall(pkg_size + pkg)
        if sent:
            raise socket.error('socket connection broken')

    def recv(self):
        """Receive message from socket.

        Returns:
            The message sent from client.
        """

        chunks = []
        bytes_recvd = 0

        # In case we don't get all 4 bytes of the prefix the first recv(),
        # this ensures we'll eventually get it intact. This while loop
        # gets the first 4 bytes and nothing more.
        while bytes_recvd < PREFIX_LEN:
            chunk = self.s.recv(min(PREFIX_LEN - bytes_recvd, PREFIX_LEN))
            if not chunk:
                raise socket.error('socket connection broken')
            chunks.append(chunk)
            bytes_recvd += len(chunk)

        # repackage together the header 4 bytes if they came separately
        # and unpack into and int
        header = ''.join(chunks)
        msglen = struct.unpack('>I', header)[0]

        # clear out the chunks list, from now on it'll contain the data sent
        del chunks[:]

        # reset bytes_recvd counter for 0 out of msglen received
        bytes_recvd = 0

        # now receive the rest of the data using the received message length
        while bytes_recvd < msglen:
            chunk = self.s.recv(min((msglen - bytes_recvd, SIZE)))
            if not chunk:
                raise socket.error('socket connection broken')
            chunks.append(chunk)
            bytes_recvd += len(chunk)

        # join all the chunks received, base64 decode, and return
        return base64.b64decode(''.join(chunks))
