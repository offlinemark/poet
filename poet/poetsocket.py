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
        pkg_size = struct.pack('>i', len(pkg))
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
        # this ensures we'll eventually get it intact
        while bytes_recvd < PREFIX_LEN:
            chunk = self.s.recv(min(PREFIX_LEN - bytes_recvd, PREFIX_LEN))
            if not chunk:
                raise socket.error('socket connection broken')
            chunks.append(chunk)
            bytes_recvd += len(chunk)

        initial = ''.join(chunks)
        msglen, initial = (struct.unpack('>I', initial[:PREFIX_LEN])[0],
                           initial[PREFIX_LEN:])
        del chunks[:]
        bytes_recvd = len(initial)
        chunks.append(initial)
        while bytes_recvd < msglen:
            chunk = self.s.recv(min((msglen - bytes_recvd, SIZE)))
            if not chunk:
                raise socket.error('socket connection broken')
            chunks.append(chunk)
            bytes_recvd += len(chunk)
        return base64.b64decode(''.join(chunks))
