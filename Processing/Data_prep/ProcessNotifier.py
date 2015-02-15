import sys
import os
sys.path.append("/opt/local/Library/Frameworks/Python.framework/Versions/2.7/lib/python2.7/site-packages/")
import psycopg2
import time

class Notifier:

    dbconnection = None
    dbcursor = None

    def __init__(self, dbconnect):
        self.dbconnection = dbconnect
        self.dbcursor = self.dbconnection.cursor()

    def addTrackRecord(self, uid, trackhash):
        try:
            self.dbcursor.execute('INSERT INTO "ProcessTracking" ("UID", "TrackHash", "StartedOn") VALUES (' + str(uid) + ', \'' + str(trackhash) + '\',' + 'to_timestamp(' + str(int(time.time())) + ')' +  ');')
            print "INFO  : added tracker to database"
            self.dbconnection.commit()
        except psycopg2.Error, e:
            print "INFO (ERROR) : failed to create track record"
            print e.pgerror

    def updateTrackRecordFinished(self, TrackHash, datasetid):
        try:
            self.dbcursor.execute('UPDATE "ProcessTracking" SET ("DatasetID", "CompletedOn", "Completed") = (' + str(datasetid) + ', ' + 'to_timestamp(' + str(int(time.time())) + '),1) WHERE "TrackHash" = \'' + TrackHash + '\';')
            print "INFO  : updated tracker to complete"
        except psycopg2.Error, e:
            print "INFO (ERROR) : failed updating track record"
            print e.pgerror
