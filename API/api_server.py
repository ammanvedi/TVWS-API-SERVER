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
    if (os.path.exists("/home/ammanvedi/cert/ssl.crt")):
        print "found ssl cert, using SSL"
        http_server = tornado.httpserver.HTTPServer(api, ssl_options=dict(certfile="/home/ammanvedi/cert/measurespace.chain.pem",keyfile="/home/ammanvedi/cert/private.key", ciphers="ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-SHA384:ECDHE-ECDSA-AES256-SHA384:ECDHE-RSA-AES256-SHA:ECDHE-ECDSA-AES256-SHA:SRP-DSS-AES-256-CBC-SHA:SRP-RSA-AES-256-CBC-SHA:DHE-DSS-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-SHA256:DHE-DSS-AES256-SHA256:DHE-RSA-AES256-SHA:DHE-DSS-AES256-SHA:DHE-RSA-CAMELLIA256-SHA:DHE-DSS-CAMELLIA256-SHA:ECDH-RSA-AES256-GCM-SHA384:ECDH-ECDSA-AES256-GCM-SHA384:ECDH-RSA-AES256-SHA384:ECDH-ECDSA-AES256-SHA384:ECDH-RSA-AES256-SHA:ECDH-ECDSA-AES256-SHA:AES256-GCM-SHA384:AES256-SHA256:AES256-SHA:CAMELLIA256-SHA:PSK-AES256-CBC-SHA:ECDHE-RSA-DES-CBC3-SHA:ECDHE-ECDSA-DES-CBC3-SHA:SRP-DSS-3DES-EDE-CBC-SHA:SRP-RSA-3DES-EDE-CBC-SHA:EDH-RSA-DES-CBC3-SHA:EDH-DSS-DES-CBC3-SHA:ECDH-RSA-DES-CBC3-SHA:ECDH-ECDSA-DES-CBC3-SHA:DES-CBC3-SHA:PSK-3DES-EDE-CBC-SHA:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-SHA256:ECDHE-ECDSA-AES128-SHA256:ECDHE-RSA-AES128-SHA:ECDHE-ECDSA-AES128-SHA:SRP-DSS-AES-128-CBC-SHA:SRP-RSA-AES-128-CBC-SHA:DHE-DSS-AES128-GCM-SHA256:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES128-SHA256:DHE-DSS-AES128-SHA256:DHE-RSA-AES128-SHA:DHE-DSS-AES128-SHA:DHE-RSA-SEED-SHA:DHE-DSS-SEED-SHA:DHE-RSA-CAMELLIA128-SHA:DHE-DSS-CAMELLIA128-SHA:ECDH-RSA-AES128-GCM-SHA256:ECDH-ECDSA-AES128-GCM-SHA256:ECDH-RSA-AES128-SHA256:ECDH-ECDSA-AES128-SHA256:ECDH-RSA-AES128-SHA:ECDH-ECDSA-AES128-SHA:AES128-GCM-SHA256:AES128-SHA256:AES128-SHA:RC4-SHA:SEED-SHA:CAMELLIA128-SHA:IDEA-CBC-SHA:PSK-AES128-CBC-SHA:ECDHE-RSA-RC4-SHA:ECDHE-ECDSA-RC4-SHA:ECDH-RSA-RC4-SHA:ECDH-ECDSA-RC4-SHA:RC4-MD5:PSK-RC4-SHA:EDH-RSA-DES-CBC-SHA:EDH-DSS-DES-CBC-SHA:DES-CBC-SHA:EXP-EDH-RSA-DES-CBC-SHA:EXP-EDH-DSS-DES-CBC-SHA:EXP-DES-CBC-SHA:EXP-RC2-CBC-MD5:EXP-RC4-MD5")) 
        sys.stdout.write("listening on 4000\n")
        http_server.listen(4000) 
        tornado.ioloop.IOLoop.instance().start()
    else:
        print "not using SSL"
        api.listen(4000)
        tornado.ioloop.IOLoop.instance().start()







