from celery import Celery
from Data_prep import GenerateChannelReadings
from Data_prep.GenerateChannelReadings import ReadingsParser
from Data_prep import DataToDB
from celery import chord
import json

app = Celery('ProcessingTask', broker='amqp://guest@localhost//', backend='redis://localhost:6379/0')
OUTPATH = "HUEHUHUEHEUE"
BANDSLIST = None
MAXF = 0.0
MINF = 0.0
UID = -1;
TH = ""

@app.task(name='ProcessingTask.Process',ignore_result=False)
def Process(inpath, outpath, uid, trackhash):
	OUTPATH = outpath
	generation_result = 1#GenerateChannelReadings.processdata(inpath, outpath, uid, trackhash)
	gen = ReadingsParser(47,2, uid, trackhash)
	bulkdata = gen.Generate(inpath)
	BANDSLIST = bulkdata["CHA"]
	MAXF = bulkdata["maxf"]
	MINF = bulkdata["minf"]
	UID = uid
	TH = trackhash
	cb = comb.subtask(kwargs={"op":outpath, "bl": bulkdata["CHA"], "maxf": bulkdata["maxf"], "minf": bulkdata["minf"],"ud":uid, "thash":trackhash})
	header = [get_ranges.s(bulkdata["DTA"][1]["Spectrum"][ts], bulkdata["CHA"], {'lat' : loc[0], 'lon' : loc[1], 'ts' : int(float(ts))} ) for ts, loc in bulkdata["DTA"][1]["Location"].iteritems()]
	result = chord(header)(cb)
@app.task(ignore_result=False)
def comb(spectra, op, bl, maxf, minf, ud, thash):
	print "INFO : About to write file"
	printToJSON(op,{"BANDS" : bl, "DATA" : spectra, "maxf": maxf, "minf": minf})
	DataToDB.processToDB(op, ud, thash)
	return 1

def printToJSON(filepath, rawdatas):
	f1 = open(filepath, "w+")
	f1.write(json.dumps(rawdatas, ensure_ascii=0))
	print "INFO : wrote file to " +  filepath
	return
@app.task(ignore_result=False)
def get_ranges(spectrum, BLF, dp):
	res = []
	print len(spectrum.keys())
	#print self.BAND_LOWER_FREQ
	for rangedict in BLF:
		hf = rangedict["UpEnd"]
		freqsinrange = [k for k,v in spectrum.items() if (float(rangedict["LowEnd"]) <= float(k) <= float(rangedict["UpEnd"]))]
		combined = 0.0
		for val in freqsinrange:
			combined += (spectrum[val])
		#print combined
		#print freqsinrange
		combined = (combined/len(freqsinrange))
		res.append(combined)
	dp["Spectrum"] = res
	return dp




