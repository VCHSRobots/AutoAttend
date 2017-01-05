#!/usr/bin/env python3
# ---------------------------------------------------------------------
# commlink.py -- communications link between client and server.
#
# Created 01/05/2017 DLB
# ---------------------------------------------------------------------

# This is python2 code that implements a socket protocol to send
# encrypted arbitary lenght messages between them, without maintining state.

import socket
import os

class ClientLink:
    def __init__(self, host, port, cipher, log):
        #self.sck = socket.socket()
        self.host = host
        self.port = port
        self.cipher = cipher
        self.log = log

    def connect(self):
        try:
            self.sck = socket.socket()
            self.sck.connect((self.host, self.port))
        except socket.error:
            self.log.logerr("Unable to connect to server (%s, %d)" %(self.host, self.port))
            os._exit(1)

    def send(self, data):
        try:
            self.sck.send(data)
        except socket.error:
            self.log.logerr("Unable to send data to server (%s, %d)" %(self.host, self.port))
            os._exit(1)

    def receive(self):
            try:
                data = self.sck.recv(2048)
                if not data:
                    self.log.logerr("No responce from server.")
                    os._exit(1)
                #log("Received data:" + data)
                return data
            except socket.error:
                self.log.logerr("Socket error on receive.")
                os._exit(1)

    def close(self):
        try:
            self.sck.close()
        except socket.error:
            self.log.logerr("Unable to close socket -- ignoring.")

    def transact(self, msg):
        self.connect()
        cmsg = self.cipher.encrypt(msg)
        self.send(cmsg)
        cdata = self.receive()
        data = self.cipher.decrypt(cdata)
        self.close()
        return data