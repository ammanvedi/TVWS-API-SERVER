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
import uuid
import hashlib



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

    #select "Timestamp", "ChannelID", "CombinedPower", ST_X(geom) AS "Lon", ST_Y(geom) AS "Lat" from "ReadingDataset" LEFT JOIN "ChannelReading" ON ("ReadingDataset"."ChannelReadingID" = "ChannelReading"."ChannelReadingID") where "ReadingDataset"."DatasetID" = 8 ORDER BY "ChannelID";
    def getDatasetsForUser(self, uid, callback):
        resobj = []
        with self.getcursor() as cur:
            try:
                cur.execute('select "DatasetID", "UserID", "DateCreated", "StartTime", "EndTime", "DataPointCount", "ChannelCount", ST_X("Datasets".geom), ST_Y("Datasets".geom), "tzid", "LowestFrequency", "HighestFrequency" from "Datasets" LEFT JOIN timezones on ("Datasets"."Timezone" = timezones."gid") where "UserID" = ' + uid)
                if cur.rowcount == 0:
                    callback(json.dumps({"QueryError" : "Unexpected : No Datasets for User"}))
                else:
                    for record in cur:
                        resobj.append({"DatasetID" : record[0], "userID": record[1], "DateCreated": self.datetimeToTimestampString(record[2]), "StartTime": self.datetimeToTimestampString(record[3]), "EndTime": self.datetimeToTimestampString(record[4]), "DataPointCount": record[5], "ChannelCount": record[6], "Lon": record[7], "Lat": record[8], "Placename" : record[9], "LF": record[10], "HF": record[11]})
                    callback(json.dumps(resobj))
            except psycopg2.Error, e:
                callback(json.dumps({"QueryError" : e.pgerror }))

    #select "UserID", "DateCreated", "StartTime", "EndTime", "DataPointCount", "ChannelCount", ST_X(geom) AS "Lon", ST_Y(geom) AS "Lat"  from "Datasets" where "DatasetID" = '8';
    def getDatasetMetadata(self, dsid, callback):
        with self.getcursor() as cur:
            try:
                cur.execute('select "UserID", "DateCreated", "StartTime", "EndTime", "DataPointCount", "ChannelCount", ST_X(geom) AS "Lon", ST_Y(geom) AS "Lat", "LowestFrequency", "HighestFrequency"  from "Datasets" where "DatasetID" = \'' + dsid + '\'')
                if cur.rowcount == 0:
                    callback(json.dumps({"QueryError" : "Unexpected : No Dataset with id Found"}))
                else:
                    if cur.rowcount > 1:
                        callback(json.dumps({"QueryError" : "Unexpected : Multiple Datasets with ID Found (Database error)"}))
                    elif cur.rowcount == 1:
                        for record in cur:
                            callback(json.dumps({"UserID" : record[0], "Created" : self.datetimeToTimestampString(record[1]), "StartTime" : self.datetimeToTimestampString(record[2]), "EndTime" : self.datetimeToTimestampString(record[3]), "PointCount": record[4], "ChannelCount" : record[5], "Lon" : record[6], "Lat" : record[7], "LF" : record[8], "HF" : record[9]}))
            except psycopg2.Error, e:
                callback(json.dumps({"QueryError" : e.pgerror }))

    def getDatasetsNear(self, lon, lat, radius,callback):
        res = []
        with self.getcursor() as cur:
            try:
                cur.execute('SELECT "UserID", "DateCreated", "StartTime", "EndTime", "DataPointCount", "ChannelCount", ST_X(geom) AS "Lon", ST_Y(geom) AS "Lat", "DatasetID", "HighestFrequency", "LowestFrequency" FROM "Datasets" WHERE ST_DWithin(geom::geography, ST_SetSRID(ST_MakePoint(' + str(lon) + ',' + str(lat) + '), 4326), '+ str(radius)+') ORDER BY "EndTime" DESC')
                if cur.rowcount == 0:
                    callback(json.dumps({"QueryError" : "Unexpected : No Datasets in region Found, try an increased search radius or different geographical area"}))
                else:
                    for record in cur:
                        res.append({"UserID" : record[0], "Created" : self.datetimeToTimestampString(record[1]), "StartTime" : self.datetimeToTimestampString(record[2]), "EndTime" : self.datetimeToTimestampString(record[3]), "PointCount": record[4], "ChannelCount" : record[5], "Lon" : record[6], "Lat" : record[7], "DatasetID" : record[8], "LF" : record[9], "HF" : record[10]})
                    callback(json.dumps(res))
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

    #
    def getChannel(self, trid, callback):
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

    #SELECT * FROM "ITUChannel" WHERE "ChannelID" IN (SELECT "ChannelID" FROM "RegionChannel" WHERE "RegionID" IN (SELECT "RegionID" FROM "Regions" WHERE gid IN (SELECT gid FROM cntry08 WHERE st_contains(cntry08.geom, ST_GeometryFromText('POINT(-0.1347394 51.5096982)',4632)))));
    #get channel defaults
    #SELECT * FROM "ITUChannel" WHERE "ChannelID" IN (SELECT "ITUChannelDefaultRef" FROM "DefaultChannels" WHERE "ITURegionRef" IN (SELECT "ITURegionRef" FROM "Regions" WHERE gid IN (SELECT gid FROM cntry08 WHERE st_contains(cntry08.geom, ST_GeometryFromText('POINT(-74.0111 40.7625 )',4632)))));
    def getChannelsForLocation(self, lng, lat, callback):
        res = []
        with self.getcursor() as cur:
            #select "DatasetID", "CompletedOn", "StartedOn", "Completed", "error", "message" from "ProcessTracking" where "TrackHash" = '1424364459.31';
            try:
                cur.execute('SELECT "ChannelID", "ChannelNumber", "LowerFrequency", "HighFrequency" FROM "ITUChannel" WHERE "ChannelID" IN (SELECT "ChannelID" FROM "RegionChannel" WHERE "RegionID" IN (SELECT "RegionID" FROM "Regions" WHERE gid IN (SELECT gid FROM cntry08 WHERE st_contains(cntry08.geom, ST_GeometryFromText(\'POINT(' + str(lng) + ' ' +  str(lat) + ')\',4632)))));')
                if cur.rowcount == 0:
                    #callback(json.dumps({"QueryError" : "Unexpected : No Track Records Found"}))
                    #was unable to find a set of specific channel allocations for this location, try to find a default setting
                    try:
                        cur.execute('SELECT "ChannelID", "ChannelNumber", "LowerFrequency", "HighFrequency" FROM "ITUChannel" WHERE "ChannelID" IN (SELECT "ITUChannelDefaultRef" FROM "DefaultChannels" WHERE "ITURegionRef" IN (SELECT "ITURegionRef" FROM "Regions" WHERE gid IN (SELECT gid FROM cntry08 WHERE st_contains(cntry08.geom, ST_GeometryFromText(\'POINT(' + str(lng) + ' ' +  str(lat) + ')\',4632)))));')
                        if cur.rowcount == 0:
                            callback(json.dumps({"QueryError" : "Could not get any channel assignments for this location, It is possible that this region is not yet suppported" }))
                        else:
                            for record in cur:
                                res.append({"ChannelID" : record[0], "ChannelNumber" : record[1], "LowEnd" : record[2], "UpEnd" : record[3]})
                            callback(json.dumps(res))
                    except psycopg2.Error, e:
                        callback(json.dumps({"QueryError" : e.pgerror }))
                else:
                    for record in cur:
                        res.append({"ChannelID" : record[0], "ChannelNumber" : record[1], "LowEnd" : record[2], "UpEnd" : record[3]})
                    callback(json.dumps(res))
            except psycopg2.Error, e:
                callback(json.dumps({"QueryError" : e.pgerror }))

    def getLastInsertedID(self):
        cur.execute("SELECT LASTVAL();")
        return cur.fetchone()[0]

    #def loginUser(self, username, password):


    def registerUser(self, email, password, fname, sname, callback):
        #generate a random hash from uuid 
        uuidgen = str(uuid.uuid1())
        print uuidgen
        hashed = hashlib.sha512(password + str(uuidgen)).hexdigest()
        with self.getcursor() as cur:
            try:
                print ('INSERT INTO "Users" ("Email", "Fname", "Sname", "PasswordHash", "GUID", "Location") VALUES (\'{0}\', \'{1}\', \'{2}\',\'{3}\', \'{4}\', \'none\')').format(email, fname, sname, hashed, uuidgen)
                cur.execute(('INSERT INTO "Users" ("Email", "Fname", "Sname", "PasswordHash", "GUID", "Location") VALUES (\'{0}\', \'{1}\', \'{2}\',\'{3}\', \'{4}\', \'none\')').format(email, fname, sname, hashed, uuidgen))
                callback(json.dumps({"QueryStatus" : "Success, should try login" }))
                cur.connection.commit()
            except psycopg2.Error, e:
                callback(json.dumps({"QueryError" : e.pgerror }))

    def createUserToken(self, userid):
        with self.getcursor() as cur:
            try:
                cur.execute(('SELECT * FROM tokens WHERE "UserID" = \'{0}\'').format(userid))
                if(cur.rowcount == 1):
                    for record in cur:
                        print record
                        return {"Token" : record[1]}
                else:
                    #should gen a new token
                    uuidgen = str(uuid.uuid1())
                    try:
                        cur.execute(('INSERT INTO tokens ("UserID", "Token") VALUES (\'{0}\', \'{1}\')').format(userid, uuidgen))
                        cur.connection.commit()
                        return {"Token" : uuidgen}
                    except psycopg2.Error, e:
                        return {"QueryError" : e.pgerror }                              
            except psycopg2.Error, e:
                return {"QueryError" : e.pgerror }

    def logoutUser(self, Token):
        with self.getcursor() as cur:
            try:
                cur.execute(('DELETE FROM tokens WHERE "Token" = \'{0}\'').format(Token))
                cur.connection.commit()
                return {"Token" : "Deleted"}
            except psycopg2.Error, e:
                return {"QueryError" : e.pgerror}     

    def checkUserToken(self, Token):
        with self.getcursor() as cur:
            try:
                cur.execute(('SELECT * FROM tokens WHERE "Token" = \'{0}\'').format(Token))
                if(cur.rowcount == 1):
                    return {"Token" : "VALID"}
                else:
                    return {"Token" : "INVALID"}
            except psycopg2.Error, e:
                return {"QueryError" : e.pgerror}

    def basicAuthUser(self, username, passw, callback):
        uuidgen = str(uuid.uuid1())
        print uuidgen
        hashed = hashlib.sha512(passw + str(uuidgen)).hexdigest()
        with self.getcursor() as cur:
            try:
                cur.execute(('SELECT * FROM "Users" WHERE "Email" = \'{0}\'').format(username))
                if(cur.rowcount == 1):
                    for record in cur:
                        print record
                        if(hashlib.sha512(passw + record[6]).hexdigest() == record[5]):
                            #create and return token
                            print "success"
                            tkn = self.createUserToken(record[0])
                            if(hasattr(tkn, "QueryError")):
                                callback(json.dumps(tkn))
                            else:
                                #token is valid
                                print "tkn is "
                                print tkn
                                callback(json.dumps({"Token" : tkn["Token"], "UserID" : record[0], "Email" : record[1], "ForeName" : record[3], "Surname" : record[2]}))
                        else:
                            callback(json.dumps({"QueryError" : "Username Or Password Incorrect" }))
                else:
                    callback(json.dumps({"QueryError" : "Username Or Password Incorrect" }))
            except psycopg2.Error, e:
                callback(json.dumps({"QueryError" : e.pgerror }))






