import sys
import os
import tornado.ioloop
import tornado.web
from tornado import gen
sys.path.append("/srv/TVWSAPI/TVWS-API-SERVER")
sys.path.append("/Users/ammanvedi/Documents/cs/year3/TVWhiteSpaceProject/PROJECT_CODE_FINAL/TVWS/Server-Python")
from Processing import ProcessingTask
import time
sys.path.append("/opt/local/Library/Frameworks/Python.framework/Versions/2.7/lib/python2.7/site-packages/")
import psycopg2
from DatabaseHelper import DBHelper
import json

psqlHelper = DBHelper();

class DataUploadHandler(tornado.web.RequestHandler):
    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
    def post(self):
        print "file uploaded"
        print "--------Adding file to rabbitmq------\n"
        trackingid = str(time.time())
        ProcessingTask.Process.delay(self.get_argument('file6.path'), "/srv/TVWSAPI/TVWS-API-SERVER" + "/Processing/WorkerResults/" + self.get_argument('file6.name'), 0, trackingid)
        response = {'trackingid' : trackingid }
        self.write(response)

class TrackHandler(tornado.web.RequestHandler):
    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
    @tornado.web.asynchronous
    @gen.coroutine
    def get(self, trackid):
        res = yield tornado.gen.Task(psqlHelper.getUploadStatus, str(trackid))
        self.write(str(res))
        self.finish()

class DatasetByIDHandler(tornado.web.RequestHandler):
    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
    @tornado.web.asynchronous
    @gen.coroutine
    def get(self, dsid):
        res = yield tornado.gen.Task(psqlHelper.getDatasetMetadata, str(dsid))
        self.write(str(res))
        self.finish()

class DatasetReadingsByIDHandler(tornado.web.RequestHandler):
    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
    @tornado.web.asynchronous
    @gen.coroutine
    def get(self, dsid):
        res = yield tornado.gen.Task(psqlHelper.getDatasetReadings, str(dsid))
        self.write(str(res))
        self.finish()

api = tornado.web.Application([
    (r"/upload", DataUploadHandler),
    (r"/measurements/track/([0-9]+\.[0-9]+)", TrackHandler),
    (r"/datasets/([0-9]+)/meta", DatasetByIDHandler),
    (r"/datasets/([0-9]+)/readings", DatasetReadingsByIDHandler)

])

if __name__ == "__main__":
    sys.stdout.write("listening on 4000\n")
    api.listen(4000)
    tornado.ioloop.IOLoop.instance().start()
