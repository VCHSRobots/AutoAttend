#!/usr/bin/env python3
# ---------------------------------------------------------------------
# cipher.py -- Simple log module for client and server. 
#
# Created 01/05/2017 DLB
# ---------------------------------------------------------------------

# This is python2 code.  It logs the input to a local file and also
# prints to the console.

from Crypto.Cipher import AES

class Cipher:
    def __init__(self, passphrase):
        if len(passphrase) >= 32: 
            passphrase = passphrase[:32]
        elif len(passphrase) >= 24:
            passphrase = passphrase[:24]
        elif len(passphrase) >= 16:
            passphrase = passphrase[:16]
        else:
            passphrase += "abcedfghijklmnopqrstuvwxyz"
            passphrase = passphrase[:16]
        self.key = passphrase
    def encrypt(self, msg):
        nadd = len(msg) % 16
        if nadd != 0 :
            nadd = 16 - nadd
        #print("Origina msg len, nadd= %d, %d.", (len(msg), nadd))
        spaces = "                                                         "
        msg += spaces[:nadd]
        cobj = AES.new(self.key)
        #print("message lenght = %d" % (len(msg)))
        return cobj.encrypt(msg) 
    def decrypt(self, cryptotext):
        cobj = AES.new(self.key)
        return cobj.decrypt(cryptotext)