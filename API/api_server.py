import sys
import os
import tornado.ioloop
import tornado.web
import tornado.httpserver
import os.path
from tornado import gen
sys.path.append("/srv/TVWSAPI/TVWS-API-SERVER")
sys.path.append("/Users/ammanvedi/Documents/cs/year3/TVWhiteSpaceProject/PROJECT_CODE_FINAL/TVWS/Server-Python")
from Processing import ProcessingTask
import time
sys.path.append("/opt/local/Library/Frameworks/Python.framework/Versions/2.7/lib/python2.7/site-packages/")
import psycopg2
from DatabaseHelper import DBHelper
import json
import ssl
from functools import wraps

def sslwrap(func):
    @wraps(func)
    def bar(*args, **kw):
        kw['ssl_version'] = ssl.PROTOCOL_TLSv1
        return func(*args, **kw)
    return bar
ssl.wrap_socket = sslwrap(ssl.wrap_socket)

psqlHelper = DBHelper();

class DataUploadHandler(tornado.web.RequestHandler):
    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
    def post(self):
        self.set_default_headers()
        print "file uploaded"
        print "--------Adding file to rabbitmq------\n"
        trackingid = str(time.time())
        print "THE USER ID"
        print self.get_argument('UID')
        ProcessingTask.Process.delay(self.get_argument('file6.path'), "/srv/TVWSAPI/TVWS-API-SERVER" + "/Processing/WorkerResults/" + self.get_argument('file6.name'), int(self.get_argument('UID')), trackingid)
        response = {'trackingid' : trackingid }
        self.write(response)

class TrackHandler(tornado.web.RequestHandler):
    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
    @tornado.web.asynchronous
    @gen.coroutine
    def get(self, trackid):
        self.set_default_headers()
        res = yield tornado.gen.Task(psqlHelper.getUploadStatus, str(trackid))
        self.write(str(res))
        self.finish()

class DatasetByIDHandler(tornado.web.RequestHandler):
    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
    @tornado.web.asynchronous
    @gen.coroutine
    def get(self, dsid):
        self.set_default_headers()
        res = yield tornado.gen.Task(psqlHelper.getDatasetMetadata, str(dsid))
        self.write(str(res))
        self.finish()

class DatasetReadingsByIDHandler(tornado.web.RequestHandler):
    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
    @tornado.web.asynchronous
    @gen.coroutine
    def get(self, dsid):
        self.set_default_headers()
        res = yield tornado.gen.Task(psqlHelper.getDatasetReadings, str(dsid))
        self.write(str(res))
        self.finish()

class DatasetsByLatLongHandler(tornado.web.RequestHandler):
    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
    @tornado.web.asynchronous
    @gen.coroutine
    def get(self, lon, lat, radius):
        self.set_default_headers()
        res = yield tornado.gen.Task(psqlHelper.getDatasetsNear, str(lon), str(lat), str(radius))
        self.write(str(res))
        self.finish()

class ChannelsByLatLong(tornado.web.RequestHandler):
    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
    @tornado.web.asynchronous
    @gen.coroutine
    def get(self, lon, lat):
        self.set_default_headers()
        res = yield tornado.gen.Task(psqlHelper.getChannelsForLocation, str(lon), str(lat))
        self.write(str(res))
        self.finish()

class ChannelsByID(tornado.web.RequestHandler):
    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
    @tornado.web.asynchronous
    @gen.coroutine
    def get(self, cid):
        self.set_default_headers()
        res = yield tornado.gen.Task(psqlHelper.getChannel, str(cid))
        self.write(str(res))
        self.finish()

class RegisterHandler(tornado.web.RequestHandler):
    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
    @tornado.web.asynchronous
    @gen.coroutine
    def post(self):
        self.set_default_headers()
        res = yield tornado.gen.Task(psqlHelper.registerUser, str(self.get_argument('email')), str(self.get_argument('password')), str(self.get_argument('sname')) , str(self.get_argument('fname')) )
        self.write(str(res))
        self.finish()

class LoginHandler(tornado.web.RequestHandler):
    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
    @tornado.web.asynchronous
    @gen.coroutine
    def post(self):
        self.set_default_headers()
        res = yield tornado.gen.Task(psqlHelper.basicAuthUser, str(self.get_argument('uname')), str(self.get_argument('pword')))
        self.write(str(res))
        self.finish()

class UserDatasetsHandler(tornado.web.RequestHandler):
    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
    @tornado.web.asynchronous
    @gen.coroutine
    def get(self, uid):
        self.set_default_headers()
        res = yield tornado.gen.Task(psqlHelper.getDatasetsForUser, uid)
        self.write(str(res))
        self.finish()


api = tornado.web.Application([
    (r"/upload", DataUploadHandler),
    (r"/upload/track/([0-9]+\.[0-9]+)", TrackHandler),
    (r"/datasets/([0-9]+)/meta", DatasetByIDHandler),
    (r"/datasets/([0-9]+)/readings", DatasetReadingsByIDHandler),
    (r"/datasets/near/(-?[0-9]+\.[0-9]+)/(-?[0-9]+\.[0-9]+)/([0-9]+)", DatasetsByLatLongHandler),
    (r"/channels/near/(-?[0-9]+\.[0-9]+)/(-?[0-9]+\.[0-9]+)", ChannelsByLatLong),
    (r"/channels/([0-9]+)", ChannelsByID),
    (r"/register", RegisterHandler),
    (r"/login", LoginHandler),
    (r"/user/([0-9]+)/datasets", UserDatasetsHandler)
])

if __name__ == "__main__":
    print ssl.PROTOCOL_SSLv3
    if (os.path.exists("/home/ammanvedi/cert/ssl.crt")):
        print "found ssl cert, using SSL"
        http_server = tornado.httpserver.HTTPServer(api, ssl_options={"certfile":"/home/ammanvedi/cert/measurespace.chain.pem","keyfile":"/home/ammanvedi/cert/private.key", "ssl_version": ssl.PROTOCOL_TLSv1}) 
        sys.stdout.write("listening on 4000\n")
        http_server.listen(4000) 
        tornado.ioloop.IOLoop.instance().start()
    else:
        print "not using SSL"
        api.listen(4000)
        tornado.ioloop.IOLoop.instance().start()







