import sys
import os
import tornado.ioloop
import tornado.web
sys.path.append("/srv/TVWSAPI/TVWS-API-SERVER")
from Processing import ProcessingTask
import time

class DataUploadHandler(tornado.web.RequestHandler):
    def post(self):
        print "file uploaded"
        print "--------Adding file to rabbitmq------\n"
        ProcessingTask.Process.delay(self.get_argument('file6.path'), "/srv/TVWSAPI/TVWS-API-SERVER" + "/Processing/WorkerResults/" + self.get_argument('file6.name'), 0, str(time.time()))

api = tornado.web.Application([
    (r"/upload", DataUploadHandler)

])

if __name__ == "__main__":
    print "listening on 4000"
    api.listen(4000)
    tornado.ioloop.IOLoop.instance().start()
