# -*- coding: utf-8 -*-
import json
import sys
import os
from math import radians, cos, sin, asin, sqrt
from shapely.geometry import shape, Point
sys.path.append("/opt/local/Library/Frameworks/Python.framework/Versions/2.7/lib/python2.7/site-packages/")
import psycopg2
from ProcessNotifier import Notifier
import re


'''
	identify bands
'''

class RegionSelector:
	ITU_COUNTRIES = None
	WORLD_COUNTRIES = None
	ITU_REGIONS = None
	dbcursor = None
	connection = None

	def __init__(self, ITUcountriesfile, Worldcountriesfile, ITUregionsfile):
		ITU_C_O = open(ITUcountriesfile)
		self.ITU_COUNTRIES = json.load(ITU_C_O)
		ITU_C_O.close()
		WORLD_C_F = open(Worldcountriesfile)
		self.WORLD_COUNTRIES = json.load(WORLD_C_F)
		WORLD_C_F.close()
		ITU_R_F = open(ITUregionsfile)
		self.ITU_REGION = json.load(ITU_R_F)
		ITU_R_F.close()
		conn_string = "host='localhost' dbname='TVWS' user='ammanvedi' password=''"
		print "INFO : connecting to database	-> ( " + conn_string + ")"
		self.connection = psycopg2.connect(conn_string)
		self.dbcursor = self.connection.cursor()
		print "INFO : Connected to Postgres DB"

	def getConnection(self):
		return self.connection

	def getITUCountries(self):
		return self.ITU_COUNTRIES

	def getWorldCountries(self):
		return self.WORLD_COUNTRIES

	def getITURegions(self):
		return self.ITU_REGIONS

	def findCountry(self, lat, lng):
		testpoint = Point(lng, lat)
		for countrygeom in self.WORLD_COUNTRIES["features"]:
			geopoly = shape(countrygeom["geometry"])
			if geopoly.contains(testpoint):
				print "INFO : found measurement country of origin"
				return countrygeom["properties"]["name"]
		return None

	def findRegion(self, countryname):
		allcapsname = countryname.upper()
		for country in self.ITU_COUNTRIES:
			if country["Country"] == allcapsname:
				print "INFO : found ITU region for country"
				return country["ITURegion"]
		return None

	def getChannels(self, ITURegionNumber):
		print "INFO : found channel list for country"
		return [self.ITU_REGION[str(ITURegionNumber)]["subregions"][0]["Channels"],self.ITU_REGION[str(ITURegionNumber)]["BandWidth"]]

	def getChannelsFromDB(self, lat, lng):
		wrapper = []
		composite = []
		print "INFO : attempting to find region channels from database"
		try:
			self.dbcursor.execute('SELECT * FROM "ITUChannel" WHERE "ChannelID" IN (SELECT "ChannelID" FROM "RegionChannel" WHERE "RegionID" IN (SELECT "RegionID" FROM "Regions" WHERE gid IN (SELECT gid FROM cntry08 WHERE st_contains(cntry08.geom, ST_GeometryFromText(\'POINT(' + str(lng) + ' ' +  str(lat) + ')\',4632)))));')
			if self.dbcursor.rowcount > 0:
				for record in self.dbcursor:
					channeldict = {"LowEnd" : record[2], "ChannelNumber" : record[1],  "UpEnd" : record[3], "ChannelID" : record[0]}
					composite.append(channeldict)
				print "INFO : found region channels"
			else:
				print "INFO : could not find specific channel assignments, defaulting to assignments for region"
				self.dbcursor.execute('SELECT * FROM "ITUChannel" WHERE "ChannelID" IN (SELECT "ITUChannelDefaultRef" FROM "DefaultChannels" WHERE "ITURegionRef" IN (SELECT "ITURegionRef" FROM "Regions" WHERE gid IN (SELECT gid FROM cntry08 WHERE st_contains(cntry08.geom, ST_GeometryFromText(\'POINT(' + str(lng) + ' ' +  str(lat) + ')\',4632)))));')
				if self.dbcursor.rowcount > 0:
					for record in self.dbcursor:
						channeldict = {"LowEnd" : record[2], "ChannelNumber" : record[1],  "UpEnd" : record[3], "ChannelID" : record[0]}
						composite.append(channeldict)
					print "INFO : found region channels from defaults"
		except psycopg2.Error, e:
			print "INFO (ERROR) : failed to find region channels, printing error;"
			print e.pgerror
		wrapper.append(composite)
		wrapper.append(8)
		return wrapper


'''
	combine powers over bands
'''

class ReadingsParser:

	DATA_FILE = None
	MIN_POWER = 47
	BAND_LOWER_FREQ = None
	CHANNEL_IDS = None
	BAND_WIDTH = 0.3
	MIN_DISTANCE = 30
	RegionID = None
	N = None
	ERRORSTATUS = 0
	TRACKID = None

	def __init__(self, minimumpower, minimumdistance, user, tracker):
		#ADD TRACK RECORD HERE!!
		self.MIN_POWER = minimumpower
		self.MIN_DISTANCE = minimumdistance
		#self.RegionID = RegionSelector("/srv/TVWSAPI/TVWS-API-SERVER" + "/Processing/Data_prep/meta/ITURegionCountries.json", "/srv/TVWSAPI/TVWS-API-SERVER" + "/Processing/Data_prep/meta/countries.geo.json", "/srv/TVWSAPI/TVWS-API-SERVER" + "/Processing/Data_prep/meta/channelallocations.json")
		self.RegionID = RegionSelector("/Users/ammanvedi/Documents/cs/year3/TVWhiteSpaceProject/PROJECT_CODE_FINAL/TVWS/Server-Python" + "/Processing/Data_prep/meta/ITURegionCountries.json", "/Users/ammanvedi/Documents/cs/year3/TVWhiteSpaceProject/PROJECT_CODE_FINAL/TVWS/Server-Python" + "/Processing/Data_prep/meta/countries.geo.json", "/Users/ammanvedi/Documents/cs/year3/TVWhiteSpaceProject/PROJECT_CODE_FINAL/TVWS/Server-Python" + "/Processing/Data_prep/meta/channelallocations.json")
		self.N = Notifier(self.RegionID.getConnection())
		self.TRACKID = tracker
		self.N.addTrackRecord(user, tracker)

	def determineBands(self, rawdatas):
		range = list()
		frequencies = list()
		BANDS = None
		for time, freqs in rawdatas[1]["Spectrum"].iteritems():
			range = freqs
			break
		for freq, power in range.iteritems():
			frequencies.append(float(freq))
		topend = max(frequencies)
		lowend = min(frequencies)
		for ts, loc in rawdatas[1]["Location"].iteritems():
			BANDS = self.RegionID.getChannelsFromDB(loc[0], loc[1])
			break
		filtered = [elem for elem in BANDS[0] if ((elem["LowEnd"] >= lowend) and (elem["UpEnd"] <= topend))]
		reduced = [self.GetBoundaries(elem) for elem in filtered if 1]
		print "INFO : selected valid bands"
		return reduced

	def GetBoundaries(self, struct):
		return {"UpEnd" : struct["UpEnd"], "LowEnd" : struct["LowEnd"], "CID" : struct["ChannelID"]}


	def Generate(self, filename):
		self.DATA_FILE = filename
		res = []
		json_file = open(self.DATA_FILE)
		try:
			data = json.load(json_file)
		except ValueError, e:
			self.ERRORSTATUS = 1
			self.N.updateTrackRecordError(self.TRACKID, "Uploaded file does not constitute valid JSON.")
			return {'FAILED' : 'JSON validation failed'}
		#strip the string of spaces and newlines
		filestring = json.dumps(data)
		filestring = re.sub("\n", "", filestring)
		filestring = filestring.replace(" ", "")
		testresult = re.search("^\\[.*,{.+,[\"”]Spectrum[\"”]:{([\"”]\\d+(\\.\\d+)?[\"”]:{([\"”]\\d+(\\.\\d+)?[\"”]:-?\\d+(\\.\\d+)?,?)+},?)+}.*,?[\"”]Location[\"”]:{([\"”]\\d+(\\.\\d+)?(\\.[f]\\d+)?[\"”]:\\[-?\\d+\\.\\d+,-?\\d+\\.\\d+(,\\d+\\.\\d+)?\\],?)+}.*}.*]" ,filestring, re.S)
		if testresult != None:
			self.BAND_LOWER_FREQ = self.determineBands(data)
			spectrum = data[1]["Spectrum"]
			print "INFO : combining readings for "+ filename+ " across valid bands..."
			for ts, loc in data[1]["Location"].iteritems():
				data_point = {'lat' : loc[0], 'lon' : loc[1], 'ts' : int(float(ts))}
				if self.farther_than(self.MIN_DISTANCE, res, data_point):
					data_point["Spectrum"] = self.get_ranges(spectrum[ts])
					res.append(data_point)
			print "INFO : finished compiling combined readings for " +  filename
			return {'BANDS' : self.BAND_LOWER_FREQ, 'DATA' : res}
		else:
			#use notifier to inform user of error
			self.ERRORSTATUS = 1
			self.N.updateTrackRecordError(self.TRACKID, "Uploaded file has incorrect format. Check documentation for valid formats.")
			return {'FAILED' : 'regular expression validator failed'}

	def get_ranges(self, spectrum):
		res = []
		for rangedict in self.BAND_LOWER_FREQ:
			hf = rangedict["UpEnd"]
			freqsinrange = [k for k,v in spectrum.items() if (float(rangedict["LowEnd"]) <= float(k) <= float(rangedict["UpEnd"]))]
			combined = 0.0
			for val in freqsinrange:
				combined += (spectrum[val])
			combined = (combined/len(freqsinrange))
			res.append(combined)
		return res

	def haversine(self, lon1, lat1, lon2, lat2):
	    """
	    Calculate the great circle distance between two points
	    on the earth (specified in decimal degrees)
	    """
	    # convert decimal degrees to radians
	    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
	    # haversine formula
	    dlon = lon2 - lon1
	    dlat = lat2 - lat1
	    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
	    c = 2 * asin(sqrt(a))
	    km = 6371.0 * c
	    return km*1000.0

	def printToJSON(self, filepath, rawdatas):
		f1 = open(filepath, "w+")
		f1.write(json.dumps(rawdatas, ensure_ascii=0))
		print "INFO : wrote file to " +  filepath

	def farther_than(self, meters, accepted, point):
		found = (x for x in accepted if self.haversine(x["lon"], x["lat"], point["lon"], point["lat"]) < meters)
		if len(list(found))  == 0:
			return 1
		if len(list(found)) > 0:
			return 0

def processdata(inf, outf, userid, trackhash):
	gen = ReadingsParser(47,30, userid, trackhash)
	gen.printToJSON(outf,gen.Generate(inf))
	if(gen.ERRORSTATUS):
		print "INFO (ERROR): processing returned an error"
		return 1;
	else:
		print "INFO : finished processing data, without error"
		return 0;

def testreg():
	reg = RegionSelector("./meta/ITURegionCountries.json", "./meta/countries.geo.json", "./meta/channelallocations.json")
	print json.dumps(reg.getChannels(reg.findRegion(reg.findCountry(52.05249, -1.757812))))
	reg.getChannelsFromDB(52.05249, -1.757812)

def testprocess():
	gen = ReadingsParser(47,30)
	gen.printToJSON("./results/manhat.json",gen.Generate("./inputs/manhattan-testdata.json"))
	print "done!"


#testprocess()
