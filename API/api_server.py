import sys
import os
import tornado.ioloop
import tornado.web
sys.path.append(os.environ["APISERVERDIRECTORY"])
from Processing import ProcessingTask

class DataUploadHandler(tornado.web.RequestHandler):
    def post(self):
        print "file uploaded"
        print self.get_argument('file6.name')
        print self.get_argument('file6.path')
        print "--------Adding file to rabbitmq------\n"
        ProcessingTask.Process.delay(self.get_argument('file6.path'), os.environ["APISERVERDIRECTORY"] + "/Processing/WorkerResults/" + self.get_argument('file6.name'))

api = tornado.web.Application([
    (r"/upload", DataUploadHandler)

])

if __name__ == "__main__":
    print "listening on 4000"
    api.listen(4000)
    tornado.ioloop.IOLoop.instance().start()
