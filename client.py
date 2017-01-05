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
import datetime
import time
from threading import Thread
import uuid
from log import initlog, log, logerr, getlog
import cipher
import commlink

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
        self.config = ClientAttendanceConfig("client_conf.json")
        initlog(self.config.LogFolder, "c", self.config.TimeZone)
        os.environ['TZ'] = self.config.TimeZone
        time.tzset() 
        log("")
        log("Client Starting Up.")
        self.config.dumptolog()
        self.cipher = cipher.Cipher(self.config.PassPhrase)
        lg = getlog()
        self.link = commlink.ClientLink(self.config.Server, self.config.Port, self.cipher, lg)

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

