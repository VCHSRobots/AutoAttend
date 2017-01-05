#!/usr/bin/env python3
# ---------------------------------------------------------------------
# server.py -- Server for attendance monitor
#
# Created 12/29/2016 DLB
# ---------------------------------------------------------------------

# This is python3 code that implements a server that listens for 
# connections from the attendance machine on a special port.  When
# a connection is made, the attendance machine can give us data
# or ask for the latest roster file. The attendance machine
# can also ask for the latest picture for each known entry in the
# roster file.

 
import socket
import json
import sys
import os
import time
import datetime
import MySQLdb
from threading import Thread
from Crypto.Cipher import AES


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
            bn = "s%04d%02d%02d.log" % (tme.year, tme.month, tme.day)
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

class ServerAttendanceConfig:

    def __init__(self,filename):
        self.filename=filename
        try:
            with open(self.filename) as data_file:
                self.data = json.load(data_file)
                self.Server = self.data["AttendanceServer"]
                self.Port = self.data["AttendancePort"]
                self.PassPhrase = self.data["SharedPassPhrase"]
                self.LogFolder = self.data["LogFolder"]
                self.TimeZone = self.data["TimeZone"]
                self.Database = self.data["Database"]
                self.dbinfo()

        except OSError:
            print("Error: Configuration file could not be opened.")
            sys.exit(1)
        except json.decoder.JSONDecodeError:
            print("Error: Invalid json in configuration file.")
            sys.exit(1)
        except KeyError:
            print("Error: missing parameters in configuration file.")
            sys.exit(1)

    def dbinfo(self):
        host = self.Database["host"]
        user = self.Database["user"]
        pw = self.Database["password"]
        db = self.Database["database"]
        return host,user,pw,db

    def printall(self):
        print("Server     = " + self.Server)
        print("Port       = " + str(self.Port))
        print("PassPhrase = " + self.PassPhrase)
        print("LogFolder  = " + self.LogFolder)
        print("TimeZone   = " + self.TimeZone)
        print("Database, user = "     + self.Database["user"])
        print("Database, password = " + self.Database["password"])
        print("Database, host = "     + self.Database["host"])
        print("Database, database = " + self.Database["database"])

    def dumptolog(self):
        log("Server     = " + self.Server)
        log("Port       = " + str(self.Port))
        log("PassPhrase = " + self.PassPhrase)
        log("LogFolder  = " + self.LogFolder)
        log("TimeZone   = " + self.TimeZone)
        log("Database, user = "     + self.Database["user"])
        log("Database, password = " + self.Database["password"])
        log("Database, host = "     + self.Database["host"])
        log("Database, database = " + self.Database["database"])        


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
        #print("Origina msg len, nadd= %d, %d.", (len(msg), nadd))
        spaces = "                                                         "
        msg += spaces[:nadd]
        cobj = AES.new(self.key)
        #print("message lenght = %d" % (len(msg)))
        return cobj.encrypt(msg) 
    def decrypt(self, cryptotext):
        cobj = AES.new(self.key)
        return cobj.decrypt(cryptotext)

class ClientThread(Thread):
 
    def __init__(self,conn,ip,port,cipher):
        Thread.__init__(self)
        self.conn = conn
        self.ip = ip
        self.port = port
        self.cipher = cipher
        log("[+] New thread started for "+ip+":"+str(port))
 
    def run(self):
        cdata = self.conn.recv(2048)
        if not cdata: 
            log("Empty message from clinet. Terminating early. ")
            return
        data = self.cipher.decrypt(cdata)
        log("Received data:" + data)
        response = '{ "MessageType" : "ServerAck", "MessageGUID" : "012983701982374", "CurrentRosterGUID" : "187019823740987" }'
        cresponse = self.cipher.encrypt(response)
        self.conn.send(cresponse)
        self.conn.close()
        log("Connection closed for "+self.ip+":"+str(self.port))

class ServerThread(Thread):

    def __init__(self, port, cipher):
        Thread.__init__(self)
        self.port = port 
        self.cipher = cipher
        self.threads = []
        self.NTotal = 0

    def run(self):
        self.tcpsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcpsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.tcpsock.bind(('localhost', self.port))
                
        while True:
            self.tcpsock.listen(4)
            log("Waiting for incoming connections...")
            (conn, (ip,port)) = self.tcpsock.accept()
            newthread = ClientThread(conn,ip,port,self.cipher)
            self.NTotal += 1
            newthread.start()
            self.threads.append(newthread)
         
        for t in self.threads:
            t.join()   

    def NClients(self):
        return len(self.threads)    

    def NTotalConnections(self):
        return self.NTotal 


class Main:
    def __init__(self):
        global Log
        self.config = ServerAttendanceConfig("server_conf.json")
        Log.init(self.config.LogFolder)
        os.environ['TZ'] = self.config.TimeZone
        time.tzset() 
        log("")
        log("Server Starting Up.")
        self.config.dumptolog()
        host,user,pw,db = self.config.dbinfo()
        self.db = MySQLdb.connect(host=host, user=user, passwd=pw, db=db)
        self.cur = self.db.cursor()
        self.cur.execute("SELECT * from junk")
        if self.cur.rowcount <= 0 :
            logerr("Database connection failure.")
            os._exit(1)
        else :
            log("Database okay.")
        self.cipher = Cipher(self.config.PassPhrase)

    def run(self):
        serverthread = ServerThread(self.config.Port, self.cipher)
        serverthread.start()
        log("Background server thread started.")
        while True:
            cmd = raw_input("Server>")
            if cmd == "exit" :
                log("Exiting due to console command.")
                os._exit(0)
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

