# -*- coding: utf-8 -*-
from ProcessingTask import Process
import json


Process.delay("./Data_prep/inputs/failtestIJ.json", "./WorkerResults/moscow-pass.json", 0, "xxxalalal")


#json_file = open("./Data_prep/inputs/Scan.json")
#data = json.load(json_file)
#filestring = json.dumps(data)

#filestring = re.sub("\n", "", filestring)
#filestring = filestring.replace(" ", "")



#print re.search("^\\[.*,{.+,[\"”]Spectrum[\"”]:{([\"”]\\d+(\\.\\d+)?[\"”]:{([\"”]\\d+(\\.\\d+)?[\"”]:-?\\d+(\\.\\d+)?,?)+},?)+}.*,?[\"”]Location[\"”]:{([\"”]\\d+(\\.\\d+)?(\\.[f]\\d+)?[\"”]:\\[-?\\d+\\.\\d+,-?\\d+\\.\\d+(,\\d+\\.\\d+)?\\],?)+}.*}.*]" ,filestring, re.S)




# ^\[.*,\s*{.+,"Spectrum":\s*{("[0-9]+":{(\n*\s*"[0-9]+\.[0-9]+":\s*-?\d+\s*,?\n*\s*)+},?)+}\s*\n*.*,"Location":\s*\n*{("[0-9]*":\[\s*\n*-?\d+\.\d+,\n*\s*-?\d+\.\d+],?)+\n*\s*}.*}.*]
