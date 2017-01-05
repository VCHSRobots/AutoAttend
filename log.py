#!/usr/bin/env python3
# ---------------------------------------------------------------------
# log.py -- Simple log module for client and server. 
#
# Created 01/05/2017 DLB
# ---------------------------------------------------------------------

# This is python2 code.  It logs the input to a local file and also
# prints to the console.

import os
import time
import datetime

class Logit:
    logfolder = ""
    def init(self, folder, prefix):
        if len(folder) <= 0 :
            raise StandardError("Folder not specified")
        if folder[-1] != '/' :
            folder += '/'
        if not os.path.exists(folder) :
            raise StandardError("Log folder (" + folder + ") does not exist.")
        self.logfolder = folder
        self.prefix = prefix
    def log(self, s):
        if self.logfolder != "":
            tme = datetime.datetime.now()
            bn = "%s%04d%02d%02d.log" % (self.prefix, tme.year, tme.month, tme.day)
            stamp =  "[%04d%02d%02d-%02d:%02d:%02d] " % (tme.year, tme.month, tme.day, tme.hour, tme.minute, tme.second)
            fn = self.logfolder + bn
            try:
                with open(fn, 'ab') as f:
                    f.write(stamp + s + "\n")
            except:
                print("Unable to write to log file (%s) -- continuing." % fn)

Log = Logit()

def initlog(folder, prefix, timezone = "US/Pacific"):
    os.environ['TZ'] = timezone
    time.tzset() 
    global Log
    Log.init(folder, prefix)

def log(s):
    print(s)
    global Log 
    Log.log(s)

def logerr(s):
    s = "Error: " + s
    print(s)
    global Log
    Log.log(s)

def getlog():
    global Log
    return Log
