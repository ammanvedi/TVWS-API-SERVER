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
from jsonschema import validate
import csv
from django.core.exceptions import ValidationError	
import time
import datetime
import calendar
import arrow



'''
	identify bands
'''

class RegionSelector:
	ITU_COUNTRIES = None
	WORLD_COUNTRIES = None
	ITU_REGIONS = None
	dbcursor = None
	connection = None

	def __init__(self):
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
		self.RegionID = RegionSelector()
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

	def generateIntermediate(self, dataO):
		#take a dataset, validate against a set of regular expressions
		#for each acceptabel file type the follwoing are needed 
		#	a regular expression that can recognise the minified stringified file
		#	a conversion function to transform the dataset into the default standard dataset
		#inital regular expression is the default case
#		filestring = json.dumps(dataO)
#		filestring = re.sub("\n", "", filestring)
#		filestring = filestring.replace(" ", "")
#		filestring = filestring.replace("\t", "")
#		print filestring
		#parser serctions follow
		print type(dataO)
		if not isinstance(dataO, list):
			print "is a csv"
			try:
				out = ""
				timeslist = []
				loclist = []
				templat = 0.0
				rowno = 0
				startval = 0
				hopval = 0.0
				Hz = ""
				sDate = " "
				sTime = " "
				out+= "["
				out+= "\"RTLSDR Scanner\","
				out+= "{"
				out+= "\"Description\": \"\","
				out+= "\"Time\": \"2014-09-14T14:36:30.292207Z\","
				out+= "\"Spectrum\": {"
				first = True
				for row in dataO:
					rowNo = 0;
					for colnum, data in enumerate(row):
						if colnum == 0:
							sDate = row[colnum]
						if colnum == 1:
							if not (row[colnum] == sTime):
								sTime = row[colnum]
								#dt = time.strptime(sDate + " " + sTime, "%Y-%m-%d %H:%M:%S")
								unixTime = arrow.get(sDate + "" + sTime, "YYYY-MM-DD HH:mm:ss").timestamp
								if first:
									first = False
								else:
									out+= "},"
								out+= "\"" + str(unixTime) + "\": {"
								timeslist.append(unixTime)
						if colnum == 2:
							startval = int(row[colnum])
						if rowNo == 4:
							hopval = float(row[colnum])
						if rowNo == 6:
							templat = float(row[colnum])
							rowNo+=1
							continue
						if rowNo == 7:
							x = [templat, float(row[colnum])]
							loclist.append(x)
							rowNo+=1
							continue
						if rowNo > 5:
							Hz = (startval + (hopval * (rowNo - 6)))/1000000
							out+= "\"" + str(Hz) + "\": " + row[colnum] + ",\n"
							#print "\"" + str(Hz) + "\": " + row[colnum] + ","
						rowNo+=1

				out+= "}"
				out+= "},"
				out+= "\"Location\": {"
				first = True

				newlist = []
				df = False
				for y in loclist:
					df = False
					for yy in newlist:
						if (yy[0] == y[0]) and (yy[1] == yy[1]):
							df = True
					if not df:
						newlist.append(y)
				for i in timeslist:
					if first:
						first = False
					else:
						out+= "],"
					ll = newlist[timeslist.index(i)]

					out+= "\"" + str(i) + "\": ["
					out+= "" + str(ll[0]) +","
					out+= "" + str(ll[1]) +","
					out+= "189.7"
				out+= "]"
				out+= "}"
				out+= "}"
				out+="]"
				out = re.sub("(,[\\n\\s]*})", "}", out)	
				#print out
				text_file = open("try.json", "w")
				text_file.write(out)
				text_file.close()			
				return json.loads(out)
			except ValidationError:
				print "INFO : COULD NOT MATCH WITH CSV"

		schema = {"$schema":"http://json-schema.org/draft-04/schema#","id":"http://jsonschema.net","type":"array","items":[{"type":"string"},{"type":"object","properties":{"Spectrum":{"type":"object","properties":{"/":{}},"patternProperties":{"^([0-9]+)+([\\.]([0-9]+))?$":{"type":"object","properties":{"/":{}},"patternProperties":{"^([0-9]+)+([\\.]([0-9]+))?$":{"type":"number"}},"additionalProperties":False}},"additionalProperties":False},"Location":{"type":"object","properties":{"/":{}},"patternProperties":{"^([0-9]+)+([\\.]([0-9]+))?$":{"type":"array","items":[{"type":"number"},{"type":"number"},{"type":"number"}],"required":["0","1"],"additionalProperties":False}},"additionalProperties":False}},"required":["Spectrum"]}],"required":["1"]}
		try:
			validate(dataO, schema)
			def transform(dataobject):
				#this is the default case
				return dataobject
			return transform(dataO)
		except ValidationError:
			print "INFO : COULD NOT MATCH WITH DEFAULT JSON SCHEMA"
		

		return None


#
#		if(re.search("^\\[.*,{.+,[\"”]Spectrum[\"”]:{([\"”]\\d+(\\.\\d+)?[\"”]:{([\"”]\\d+(\\.\\d+)?[\"”]:-?\\d+(\\.\\d+)?,?)+},?)+}.*,?[\"”]Location[\"”]:{([\"”]\\d+(\\.\\d+)?(\\.[f]\\d+)?[\"”]:\\[-?\\d+\\.\\d+,-?\\d+\\.\\d+(,\\d+\\.\\d+)?\\],?)+}.*}.*]" ,filestring, re.S) != None):
#			print "RE succ"
#			def transform(dataobject):
#				#this is the default case
#				return dataobject
#			return transform(dataO)
#		#cannot assign any parser model
#		print "RE not succ"
#		return None;


	def Generate(self, filename):
		self.DATA_FILE = filename
		res = []
		json_file = open(self.DATA_FILE)
		try:
			data = json.load(json_file)
		except ValueError:
			print "there is valuerror"
			try:
				data = csv.reader(open(self.DATA_FILE))

			except Error:
				print "there is error"
				self.ERRORSTATUS = 1
				self.N.updateTrackRecordError(self.TRACKID, "Uploaded file does not constitute valid JSON or CSV.")
				print "FAILED : JSON or CSV validation failed"
				return {'FAILED' : 'JSON or CSV validation failed'}
		#strip the string of spaces and newlines
		data = self.generateIntermediate(data)
		if data != None:
			self.BAND_LOWER_FREQ = self.determineBands(data)
			spectrum = data[1]["Spectrum"]
			high = max(data[1]["Spectrum"][data[1]["Spectrum"].keys()[0]].keys())
			low =  min(data[1]["Spectrum"][data[1]["Spectrum"].keys()[0]].keys())
			print "INFO : combining readings for "+ filename+ " across valid bands..."
			for ts, loc in data[1]["Location"].iteritems():
				data_point = {'lat' : loc[0], 'lon' : loc[1], 'ts' : int(float(ts))}
				if self.farther_than(self.MIN_DISTANCE, res, data_point):
					data_point["Spectrum"] = self.get_ranges(spectrum[ts])
					res.append(data_point)
			print "INFO : finished compiling combined readings for " +  filename
			return {'BANDS' : self.BAND_LOWER_FREQ, 'DATA' : res, 'maxf' : high, 'minf' : low}
		else:
			#use notifier to inform user of error
			self.ERRORSTATUS = 1
			self.N.updateTrackRecordError(self.TRACKID, "Uploaded file has incorrect format. Check documentation for valid formats.")
			return {'FAILED' : 'regular expression validator failed'}

	def get_ranges(self, spectrum):
		res = []
		#print self.BAND_LOWER_FREQ
		for rangedict in self.BAND_LOWER_FREQ:
			hf = rangedict["UpEnd"]
			freqsinrange = [k for k,v in spectrum.items() if (float(rangedict["LowEnd"]) <= float(k) <= float(rangedict["UpEnd"]))]
			combined = 0.0
			for val in freqsinrange:
				combined += (spectrum[val])
			#print combined
			#print freqsinrange
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
		#print accepted
		self.average_nearpoints
		found = (x for x in accepted if self.haversine(x["lon"], x["lat"], point["lon"], point["lat"]) < meters)
		if len(list(found))  == 0:
			return 1
		if len(list(found)) > 0:
			return 0
	def average_nearpoints(self, meters, accepted, point):
		for idx, x in accepted:
			if (self.haversine(x["lon"], x["lat"], point["lon"], point["lat"]) < meters):
				newpoint = point
				for idxx, y in newpoint[0]["spectrum"]:
					newpoint[0]["spectrum"][idxx] = (newpoint[0]["spectrum"][idxx] + accepted[idx][0]["spectrum"][idxx])/2
				accepted[idx][0] = newpoint



def processdata(inf, outf, userid, trackhash):
	gen = ReadingsParser(47,2, userid, trackhash)
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
