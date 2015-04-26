# -*- coding: utf-8 -*-
from ProcessingTask import Process
import json




#Process.delay("/Users/ammanvedi/Downloads/tunnel.csv", "/Users/ammanvedi/Desktop/bartsstest.json", 0, "xxxrrralalal")

	
#Process.delay("/Users/ammanvedi/Desktop/track4-miasto.csv", "/Users/ammanvedi/Desktop/bartteqqqst.json", 0, "xxxwwwalalal")

#Process.delay("/Users/ammanvedi/Desktop/lift-loc-fixed.json", "/Users/ammanvedi/Desktop/barteeetest.json", 0, "xxxaeeelalal")

Process.delay("/Users/ammanvedi/Downloads/track3-korek.csv", "/Users/ammanvedi/Desktop/barttestrtt.json", 0, "xxxasslalal")

#json_file = open("./Data_prep/inputs/Scan.json")
#data = json.load(json_file)
#filestring = json.dumps(data)

#filestring = re.sub("\n", "", filestring)
#filestring = filestring.replace(" ", "")



#print re.search("^\\[.*,{.+,[\"”]Spectrum[\"”]:{([\"”]\\d+(\\.\\d+)?[\"”]:{([\"”]\\d+(\\.\\d+)?[\"”]:-?\\d+(\\.\\d+)?,?)+},?)+}.*,?[\"”]Location[\"”]:{([\"”]\\d+(\\.\\d+)?(\\.[f]\\d+)?[\"”]:\\[-?\\d+\\.\\d+,-?\\d+\\.\\d+(,\\d+\\.\\d+)?\\],?)+}.*}.*]" ,filestring, re.S)




# ^\[.*,\s*{.+,"Spectrum":\s*{("[0-9]+":{(\n*\s*"[0-9]+\.[0-9]+":\s*-?\d+\s*,?\n*\s*)+},?)+}\s*\n*.*,"Location":\s*\n*{("[0-9]*":\[\s*\n*-?\d+\.\d+,\n*\s*-?\d+\.\d+],?)+\n*\s*}.*}.*]
