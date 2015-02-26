import json

class ReadingSet():
    Channels = {}

    def __init__(self):
        self.Channels = {}

    def addChannelReading(self, cid, dataobject):
        if cid in self.Channels:
            #is in add reading to array
            self.Channels[cid].append(dataobject)
        else:
            #not in, create array and add reading
            self.Channels[cid] = []
            self.Channels[cid].append(dataobject)

    def getObject(self):
        return self.Channels

    def getObjectJSON(self):
        return json.dumps(self.Channels)
