#!/usr/bin/env python3
# ---------------------------------------------------------------------
# client.py -- Client for attendance monitor
#
# Created 01/02/2017 DLB
# ---------------------------------------------------------------------

# This is python2 code that implements a client that interacts with a 
# server located in the clowd.  It sends scans to the server and keeps
# the roster up to date.

 
import socket
import json
import sys
import os
import time
import datetime
import MySQLdb
from threading import Thread
from Crypto.Cipher import AES
import uuid


testscan = '''
{
    "MessageType" :"Scan",
    "MessageUuid" : "10980980198743",
    "Machine" : "EpicAttendanceScanner01",
    "ScanUuid" : "91-9893-108971093287-123978",
    "ScanTime" : "2017-07-07_12:57:22",
    "ScanText" : "AE C0023b"
}          
'''

class Logit:
    logfolder = ""
    def init(self, folder):
        if len(folder) <= 0 :
            print("Log folder not specified.")
            os._exit(1)
        if folder[-1] != '/' :
            folder += '/'
        if not os.path.exists(folder) :
            print("Log folder (" + folder + ") does not exist.")
            os._exit(1)
        self.logfolder = folder
    def log(self, s):
        if self.logfolder != "":
            tz = datetime.tzinfo()
            tme = datetime.datetime.now()
            bn = "c%04d%02d%02d.log" % (tme.year, tme.month, tme.day)
            stamp =  "[%04d%02d%02d-%02d:%02d:%02d] " % (tme.year, tme.month, tme.day, tme.hour, tme.minute, tme.second)
            fn = self.logfolder + bn
            try:
                with open(fn, 'ab') as f:
                    f.write(stamp + s + "\n")
            except:
                print("Unable to write to log file (%s)." % fn)

Log = Logit()
def log(s):
    print(s)
    global Log 
    Log.log(s)

def logerr(s):
    s = "Error: " + s
    print(s)
    global Log
    Log.log(s)

class Cipher:
    def __init__(self, passphrase):
        if len(passphrase) < 16:
            log("PassPhrase must be at least 16 chars long.")
            os._exit(1)
        self.key = passphrase[:16]
    def encrypt(self, msg):
        nadd = len(msg) % 16
        if nadd != 0 :
            nadd = 16 - nadd
        spaces = "                                                         "
        msg += spaces[:nadd]
        cobj = AES.new(self.key)
        return cobj.encrypt(msg) 
    def decrypt(self, cryptotext):
        cobj = AES.new(self.key)
        return cobj.decrypt(cryptotext)



class ClientAttendanceConfig:

    def __init__(self,filename):
        self.filename=filename
        try:
            with open(self.filename) as data_file:
                self.data = json.load(data_file)
                self.Server = self.data["AttendanceServer"]
                self.Port = self.data["AttendancePort"]
                self.PassPhrase = self.data["SharedPassPhrase"]
                self.ScanFolder = self.data["ScanFolder"]
                self.LogFolder = self.data["LogFolder"]
                self.TimeZone = self.data["TimeZone"]

        except OSError:
            print("Error: Configuration file could not be opened.")
            sys.exit(1)
        except json.decoder.JSONDecodeError:
            print("Error: Invalid json in configuration file.")
            sys.exit(1)
        except KeyError:
            print("Error: missing parameters in configuration file.")
            sys.exit(1)

    def printall(self):
        print("Server     = " + self.Server)
        print("Port       = " + str(self.Port))
        print("PassPhrase = " + self.PassPhrase)
        print("LogFolder  = " + self.LogFolder)
        print("ScanFolder = " + self.ScanFolder)
        print("TimeZone   = " + self.TimeZone)

    def dumptolog(self):
        log("Server     = " + self.Server)
        log("Port       = " + str(self.Port))
        log("PassPhrase = " + self.PassPhrase)
        log("LogFolder  = " + self.LogFolder)
        log("ScanFolder = " + self.ScanFolder)
        log("TimeZone   = " + self.TimeZone)


class DataLink:
    def __init__(self, host, port, cipher):
        #self.sck = socket.socket()
        self.host = host
        self.port = port
        self.cipher = cipher

    def connect(self):
        try:
            self.sck = socket.socket()
            self.sck.connect((self.host, self.port))
        except socket.error:
            logerr("Unable to connect to server (%s, %d)" %(self.host, self.port))
            os._exit(1)

    def send(self, data):
        try:
            self.sck.send(data)
        except socket.error:
            logerr("Unable to send data to server (%s, %d)" %(self.host, self.port))
            os._exit(1)

    def receive(self):
            try:
                data = self.sck.recv(2048)
                if not data:
                    logerr("No responce from server.")
                    os._exit(1)
                #log("Received data:" + data)
                return data
            except socket.error:
                logerr("Socket error on receive.")
                os._exit(1)

    def close(self):
        try:
            self.sck.close()
        except socket.error:
            logerr("Unable to close socket -- ignoring.")

    def transact(self, msg):
        self.connect()
        cmsg = self.cipher.encrypt(msg)
        self.send(cmsg)
        cdata = self.receive()
        data = self.cipher.decrypt(cdata)
        self.close()
        return data

def GetTimeString():
    d = datetime.datetime.now()
    return "%04d-%02d-%02dT%02d:%02d:%02d" % (d.year, d.month, d.day, d.hour, d.minute, d.second)

class ScanMsg:
    def __init__(self, scanuuid, scantime, scantext):
        self.data = {"ScanUuid" : scanuuid, 'ScanTime' : scantime, 'ScanText' : scantext}
        self.data["MessageType"] = "Scan"
        self.data["MessageUuid"] = uuid.uuid4().hex
    def getjson(self):
        return json.dumps(self.data)

class Main:
    def __init__(self):
        global Log
        self.config = ClientAttendanceConfig("client_conf.json")
        Log.init(self.config.LogFolder)
        os.environ['TZ'] = self.config.TimeZone
        time.tzset() 
        log("")
        log("Client Starting Up.")
        self.config.dumptolog()
        self.cipher = Cipher(self.config.PassPhrase)
        self.link = DataLink(self.config.Server, self.config.Port, self.cipher)

    def run(self):
        while True:
            cmd = raw_input("Client>")
            if cmd == "exit" :
                log("Exiting due to console command.")
                os._exit(0)
            if cmd == "scan" :
                log("Sending test scan due to console command.")
                scan = ScanMsg(uuid.uuid4().hex, GetTimeString(), "AE C0023b")
                outdata = self.link.transact(scan.getjson())
                log("Server Response = %s" % (outdata))
            if cmd == "status" :
                print("Number of current connections = " + str(serverthread.NClients()))
                print("Number of total connections   = " + str(serverthread.NTotalConnections()))
            if cmd == "config" :
                self.config.printall()

# ---------------------------------------------------------------------
# Main program starts here...

if __name__ == "__main__":
    app = Main()
    app.run()

# -------------------------------
# Old test code
## import socket
## s = socket.socket()         # Create a socket object
## host = socket.gethostname() # Get local machine name
## host = "localhost"
## port = 23456                # Reserve a port for your service.
## 
## s.connect((host, port))
## b = str.encode("Connected to you.\n")
## s.send(b)
## #print s.recv(1024)
## s.close                     # Close the socket when done

