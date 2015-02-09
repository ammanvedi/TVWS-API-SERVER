import json
from math import radians, cos, sin, asin, sqrt

DATA_FILE = "Scan.rfs"
MIN_POWER = 47
BAND_LOWER_FREQ = [ 945.00, 945.74, 946.18, 946.94, 947.60, 948.26, 948.84, 949.17 ]
BAND_WIDTH = 0.3
MIN_DISTANCE = 30

def load_data():
	res = []
	json_file = open(DATA_FILE)
	data = json.load(json_file)
	spectrum = data[1]["Spectrum"]
	for ts, loc in data[1]["Location"].iteritems():
		data_point = {'lat' : loc[0], 'lon' : loc[1], 'ts' : int(float(ts))}
		print data_point
		if farther_than(MIN_DISTANCE, res, data_point):
			print "found a point that was far enough away"
			data_point["Spectrum"] = get_ranges(spectrum[ts]) 
			res.append(data_point)
		else:
			print "found a point tooo close to others"
	return res

def get_ranges(spectrum):
	res = []
	for lf in BAND_LOWER_FREQ:
		hf = lf + BAND_WIDTH
		freqsinrange = [k for k,v in spectrum.items() if (float(lf) <= float(k) <= float(hf))]
		combined = 0.0
		for val in freqsinrange:
			combined += MIN_POWER + spectrum[val] 
		res.append(combined)
	return res

def haversine(lon1, lat1, lon2, lat2):
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
    km = 6371 * c
    return km*1000
    
  
def farther_than(meters, accepted, point):
	found = (x for x in accepted if haversine(x["lon"], x["lat"], point["lon"], point["lat"]) < meters)
	if len(list(found))  == 0:
		return 1
	if len(list(found)) > 0:
		return 0
		
def determineRegion(lat, lng)
	

def testgen
	print json.dumps(load_data(), ensure_ascii=0)
	
	
	
	
	

	
	
	
	
	