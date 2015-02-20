#
#   DatabaseHelper.py
#
#   Amman Vedi - 2015
#   Contains database query functions + connection pools
#   that are used in the api
#
#

from __future__ import with_statement
import tornado.ioloop
import sys
sys.path.append("/opt/local/Library/Frameworks/Python.framework/Versions/2.7/lib/python2.7/site-packages/")
import psycopg2
import psycopg2.pool
from contextlib import contextmanager
import time
import tornado.concurrent
import concurrent.futures
import json
from APIResponseObjects import ReadingSet



class DBHelper:

    dbpool = None
    CONNECTIONSTR = "host='localhost' dbname='TVWS' user='ammanvedi' password=''"

    def __init__(self):
        self.dbpool = psycopg2.pool.SimpleConnectionPool(1,10,self.CONNECTIONSTR)
        print "INFO : connecting to database	-> ( " + self.CONNECTIONSTR + ")"
        print "INFO : Connected to Postgres DB"

    @contextmanager
    def getcursor(self):
        con = self.dbpool.getconn()
        try:
            yield con.cursor()
        finally:
            self.dbpool.putconn(con)

    def datetimeToTimestampString(self, dt):
        if dt == None:
            return None
        else:
            return str(dt.strftime("%s"))

    #select "Timestamp", "ChannelID", "CombinedPower", ST_X(geom) AS "Lon", ST_Y(geom) AS "Lat" from "ReadingDataset" LEFT JOIN "ChannelReading" ON ("ReadingDataset"."ChannelReadingID" = "ChannelReading"."ChannelReadingID") where "ReadingDataset"."DatasetID" = 8 ORDER BY "ChannelID";
    def getDatasetReadings(self, dsid, callback):
        resobj = ReadingSet()
        with self.getcursor() as cur:
            try:
                cur.execute('select "Timestamp", "ChannelID", "CombinedPower", ST_X(geom) AS "Lon", ST_Y(geom) AS "Lat" from "ReadingDataset" LEFT JOIN "ChannelReading" ON ("ReadingDataset"."ChannelReadingID" = "ChannelReading"."ChannelReadingID") where "ReadingDataset"."DatasetID" =\'' + dsid + '\''  )
                if cur.rowcount == 0:
                    callback(json.dumps({"QueryError" : "Unexpected : No Readings were found for thsi dataset"}))
                else:
                    for record in cur:
                        resobj.addChannelReading(record[1],{"Timestamp" : self.datetimeToTimestampString(record[0]), "CombinedPower" : record[2], "Lon" : record[3], "Lat" : record[4]})
                callback(resobj.getObjectJSON())
            except psycopg2.Error, e:
                callback(json.dumps({"QueryError" : e.pgerror }))

    #select "UserID", "DateCreated", "StartTime", "EndTime", "DataPointCount", "ChannelCount", ST_X(geom) AS "Lon", ST_Y(geom) AS "Lat"  from "Datasets" where "DatasetID" = '8';
    def getDatasetMetadata(self, dsid, callback):
        with self.getcursor() as cur:
            try:
                cur.execute('select "UserID", "DateCreated", "StartTime", "EndTime", "DataPointCount", "ChannelCount", ST_X(geom) AS "Lon", ST_Y(geom) AS "Lat"  from "Datasets" where "DatasetID" = \'' + dsid + '\'')
                if cur.rowcount == 0:
                    callback(json.dumps({"QueryError" : "Unexpected : No Dataset with id Found"}))
                else:
                    if cur.rowcount > 1:
                        callback(json.dumps({"QueryError" : "Unexpected : Multiple Datasets with ID Found (Database error)"}))
                    elif cur.rowcount == 1:
                        for record in cur:
                            callback(json.dumps({"UserID" : record[0], "Created" : self.datetimeToTimestampString(record[1]), "StartTime" : self.datetimeToTimestampString(record[2]), "EndTime" : self.datetimeToTimestampString(record[3]), "PointCount": record[4], "ChannelCount" : record[5], "Lon" : record[6], "Lat" : record[7]}))
            except psycopg2.Error, e:
                callback(json.dumps({"QueryError" : e.pgerror }))


    def getUploadStatus(self, trid, callback):
        res = []
        with self.getcursor() as cur:
            #select "DatasetID", "CompletedOn", "StartedOn", "Completed", "error", "message" from "ProcessTracking" where "TrackHash" = '1424364459.31';
            try:
                cur.execute('select "DatasetID", "CompletedOn", "StartedOn", "Completed", "error", "message" from "ProcessTracking" where "TrackHash" = \''+ str(trid) +'\'')
                if cur.rowcount == 0:
                    callback(json.dumps({"QueryError" : "Unexpected : No Track Records Found"}))
                else:
                    if cur.rowcount > 1:
                        callback(json.dumps({"QueryError" : "Unexpected : Multiple Track Records Found"}))
                    elif cur.rowcount == 1:
                        for record in cur:
                            print record
                            callback(json.dumps({"DatasetID" : record[0], "CompletedOn" : self.datetimeToTimestampString(record[1]), "StartedOn" : self.datetimeToTimestampString(record[2]), "Completed" : record[3], "Error": record[4], "Message" : record[5]}))
            except psycopg2.Error, e:
                callback(json.dumps({"QueryError" : e.pgerror }))


    def testq(self, callback):
        res = []
        with self.getcursor() as cur:
            cur.execute("select * from \"ProcessTracking\"")
            for record in cur:
                res.append(record)
            print "time end of query " + str(time.time())
            callback(res)

    def testp(self, callback):
        callback("sdsdsdsd")
