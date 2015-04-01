from GenerateChannelReadings import RegionSelector
from ProcessNotifier import Notifier
import sys
import os
import json
import time
sys.path.append("/opt/local/Library/Frameworks/Python.framework/Versions/2.7/lib/python2.7/site-packages/")
import psycopg2

class databaseStore:

    RegionID = None
    dbcursor = None
    connection = None
    UID = None
    TRACKHASH = None
    Notify = None

    def __init__(self, userid, trackhash):
        conn_string = "host='localhost' dbname='TVWS' user='ammanvedi' password=''"
        print "INFO :  attempting connection to database -> ( %s )" % (conn_string)
        self.connection = psycopg2.connect(conn_string)
        self.dbcursor = self.connection.cursor()
        print "INFO : Connected to Postgres DB\n"
        self.UID = userid
        self.TRACKHASH = trackhash
        print "INFO : beginning processing data for usr " + str(self.UID) + " with trackhash " + self.TRACKHASH
        self.Notify = Notifier(self.connection)


    def loadProcessedToDB(self, filepath):
        #load the json data
        CHANNELCOUNT = 0
        DATAPOINTCOUNT = 0
        DATECREATED = None
        TIMEZONEID = 0
        StartTime = float('inf')
        EndTime = 0
        AVGPOINT = None
        FILE = open(filepath)
        JSONFILE = json.load(FILE)
        CR_DB_IDS = []
        FILE.close()
        #read the json, compile the insert
        print "INFO : adding channel readings to database"
        for idxs, point in enumerate(JSONFILE["DATA"]):
            for idx, combinedreading in enumerate(point["Spectrum"]):
                #print str(JSONFILE["BANDS"][idx]["CID"]) + " | " + str(combinedreading) + " MHz | (" + str(point["lon"]) + " " + str(point["lat"]) + " | " + "to_timestamp(" + str(point["ts"]) + ")"
                self.addChannelReading(str(JSONFILE["BANDS"][idx]["CID"]), str(combinedreading), str(point["lat"]) , str(point["lon"]), str(point["ts"]))
                CR_DB_IDS.append(self.getLastInsertedID())
            if point["ts"] > EndTime:
                EndTime = point["ts"]
            if point["ts"] < StartTime:
                StartTime = point["ts"]
            if idxs == (len(JSONFILE["DATA"])-1):
                #last point use it to determine the tz
                self.dbcursor.execute('SELECT gid FROM timezones WHERE ST_Contains(geom, ST_GeometryFromText(\'POINT(' + str(point["lon"]) + ' ' +  str(point["lat"]) + ')\',4326));')
                TIMEZONEID = self.dbcursor.fetchone()[0]
                AVGPOINT = {"LAT" : point["lat"], "LON" : point["lon"]}
        CHANNELCOUNT = len(JSONFILE["BANDS"])
        DATAPOINTCOUNT = len(JSONFILE["DATA"])
        DATECREATED = time.time()
        print "INFO : generated dataset metadata"
        print " | channel count                : " + str(CHANNELCOUNT)
        print " | data point count             : " + str(DATAPOINTCOUNT)
        print " | date createed                : " + "to_timestamp(" + str(int(DATECREATED)) + ")"
        print " | dataset location thumbnail   : " + json.dumps(AVGPOINT)
        print " | start time                   : " + "to_timestamp(" + str(StartTime) + ")"
        print " | end time                     : " + "to_timestamp(" + str(EndTime) + ")"
        print " | timezone ID                  : " + str(TIMEZONEID)
        print "INFO : creating dataset entry and linking readings to dataset"
        self.addDataset(CR_DB_IDS, self.UID, CHANNELCOUNT, DATAPOINTCOUNT, DATECREATED, StartTime, EndTime, AVGPOINT["LAT"], AVGPOINT["LON"], TIMEZONEID, JSONFILE['minf'], JSONFILE['maxf'])
        print "INFO : committing all additions to database"
        #UPDATE TRACKER HERE (FINISHED)
        #get the id of the dataset just added, and update tracker
        self.Notify.updateTrackRecordFinished(self.TRACKHASH, self.getLastInsertedID())
        self.connection.commit()
        self.connection.close()

    def addChannelReading(self, ChannelID, CombinedPower, lat, lon , Time):
        self.dbcursor.execute('INSERT INTO "ChannelReading" ("ChannelID", "CombinedPower", geom, "Timestamp") VALUES ('+ ChannelID +','+ CombinedPower +', ST_GeometryFromText(\'POINT(' + lon + ' ' +  lat + ')\',4326), to_timestamp(' + Time +  '));')
        #print 'INSERT INTO "ChannelReading" ("ChannelID", "CombinedPower", geom, "Timestamp") VALUES ('+ ChannelID +','+ CombinedPower +', ST_GeometryFromText(\'POINT(' + lon + ' ' +  lat + ')\',4326), to_timestamp(' + Time +  '));'
        #self.connection.commit()

    def addDataset(self, CRIDlist, uid, cc, dpc, dc, st, et, aplat, aplon, tz, minf, maxf):
        #print 'INSERT INTO "Datasets" ("ChannelCount", "DataPointCount", "DateCreated", "EndTime", geom, "StartTime", "Timezone", "UserID") VALUES ( ' + str(cc) + ', ' + str(dpc) + ', ' + 'to_timestamp(' + str(int(dc)) + ')' + ', ' + 'to_timestamp(' + str(et) + ')' + ', ' + 'ST_GeometryFromText(\'POINT(' + str(aplon) + ' ' +  str(aplat) + ')\',4326)' + ', ' + 'to_timestamp(' + str(st) + ')' + ', ' + str(tz) + ', ' + str(uid) + ');'
        try:
            self.dbcursor.execute('INSERT INTO "Datasets" ("ChannelCount", "DataPointCount", "DateCreated", "EndTime", geom, "StartTime", "Timezone", "UserID", "LowestFrequency", "HighestFrequency") VALUES ( ' + str(cc) + ', ' + str(dpc) + ', ' + 'to_timestamp(' + str(int(dc)) + ')' + ', ' + 'to_timestamp(' + str(et) + ')' + ', ' + 'ST_GeometryFromText(\'POINT(' + str(aplon) + ' ' +  str(aplat) + ')\',4326)' + ', ' + 'to_timestamp(' + str(st) + ')' + ', ' + str(tz) + ', ' + str(uid) + ', ' +  str(minf)+ ', ' + str(maxf) +  ');')
            dsid = self.getLastInsertedID()
            for crid in CRIDlist:
                self.relateDStoCR(dsid, crid)
        except psycopg2.Error, e:
            print e.pgerror
        #print json.dumps(CRIDlist)

    def relateDStoCR(self, DSID, CRID):
        try:
            self.dbcursor.execute('INSERT INTO "ReadingDataset" ("ChannelReadingID", "DatasetID") VALUES (' + str(CRID) + ', ' + str(DSID) + ')')
        except psycopg2.Error, e:
            print e.pgerror

    def getLastInsertedID(self):
        self.dbcursor.execute("SELECT LASTVAL();")
        return self.dbcursor.fetchone()[0]

    def addRegionsFromFile(self, file):
        JSONCHANNELS = open(file)
        loaded = json.load(JSONCHANNELS)
        for channeldict in loaded:
            self.processChannelSet(channeldict[0])

    def addDefaultChannelsFromFile(self, file):
        INFILE = open(file)
        JSONDEFAULTS = json.load(INFILE)
        for regionkey in JSONDEFAULTS:
            for channelinfo in JSONDEFAULTS[regionkey]["Channels"]:
                self.addDefaultChannel(channelinfo["ChannelNumber"], channelinfo["LowEnd"], channelinfo["UpEnd"], regionkey)
        self.connection.commit()

    def addDefaultChannel(self, CHANNELNUM, LOWEND, HIGHEND, ASSIGNTOREGION):
        self.dbcursor.execute('INSERT INTO "ITUChannel" ("ChannelNumber", "HighFrequency", "LowerFrequency") VALUES ( ' + str(CHANNELNUM) + ',' + str(HIGHEND) + ',' + str(LOWEND) + ')')
        print 'INSERT INTO "ITUChannel" ("ChannelNumber", "HighFrequency", "LowerFrequency") VALUES ( ' + str(CHANNELNUM) + ',' + str(HIGHEND) + ',' + str(LOWEND) + ')'
        self.dbcursor.execute('SELECT LASTVAL()')
        inserted_channel_id = self.dbcursor.fetchone()[0] #get real value here
        self.dbcursor.execute('INSERT INTO "DefaultChannels" ("ITUChannelDefaultRef", "ITURegionRef") VALUES ( ' + str(inserted_channel_id) + ',' + str(ASSIGNTOREGION) + ')')
        print 'INSERT INTO "DefaultChannels" ("ITUChannelDefaultRef", "ITURegionRef") VALUES ( ' + str(inserted_channel_id) + ',' + str(ASSIGNTOREGION) + ')'

    def addRegions(self):
        self.RegionID = RegionSelector("/Users/ammanvedi/Documents/cs/year3/TVWhiteSpaceProject/PROJECT_CODE_FINAL/TVWS/Server-Python" + "/Processing/Data_prep/meta/ITURegionCountries.json", "/Users/ammanvedi/Documents/cs/year3/TVWhiteSpaceProject/PROJECT_CODE_FINAL/TVWS/Server-Python" + "/Processing/Data_prep/meta/countries.geo.json", "/Users/ammanvedi/Documents/cs/year3/TVWhiteSpaceProject/PROJECT_CODE_FINAL/TVWS/Server-Python" + "/Processing/Data_prep/meta/channelallocations.json")
        for ITUCountry in self.RegionID.getITUCountries():
            for country in self.RegionID.getWorldCountries()["features"]:
                if country["properties"]["name"].upper() == ITUCountry["Country"]:
                    self.dbcursor.execute('SELECT gid, unshrtnam from world where unshrtnam = \''+ country["properties"]["name"] +'\';')
                    if self.dbcursor is None:
                        print "didnt get "
                    else:
                        x = self.dbcursor.fetchone()[0]
                        print x
                        print ITUCountry["Country"]
                        print ITUCountry["ITURegion"]
                        print '-------------------'
                        self.dbcursor.execute('INSERT INTO "Regions" (gid, "ITURegionRef") VALUES ('+ str(x) +','+ str(ITUCountry["ITURegion"]) +')')
        self.connection.commit()

    def addChannel(self, APPLIEDREGIONS, CHANNELNUM, LOWEND, HIGHEND):
        self.dbcursor.execute('INSERT INTO "ITUChannel" ("ChannelNumber", "HighFrequency", "LowerFrequency") VALUES ( ' + str(CHANNELNUM) + ',' + str(HIGHEND) + ',' + str(LOWEND) + ')')
        self.dbcursor.execute('SELECT LASTVAL()')
        inserted_channel_id = self.dbcursor.fetchone()[0] #get real value here
        for applyto in APPLIEDREGIONS:
            self.dbcursor.execute('SELECT "RegionID" FROM "Regions" WHERE gid = ' + str(applyto))
            x = self.dbcursor.fetchone()[0] #the regionid
            self.dbcursor.execute('INSERT INTO "RegionChannel" ("ChannelID", "RegionID") VALUES ( ' + str(inserted_channel_id) + ',' + str(x) + ')')
        self.connection.commit()

    def processChannelSet(self, channelset):
        for channel in channelset["Channels"]:
            self.addChannel(channelset["AppliesToRegions"], channel["ChannelNumber"], channel["LowEnd"], channel["UpEnd"])

def processToDB(inputfilepath, uid, th):
    dbs = databaseStore(uid, th)
    dbs.loadProcessedToDB(inputfilepath)
    print "INFO : finished passing data to postGIS"

def test():
    dbs = databaseStore()
    dbs.addDefaultChannelsFromFile("./meta/defaults.json")
