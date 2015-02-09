import sys
import os
import tornado.ioloop
import tornado.web
sys.path.append(os.environ["APISERVERDIRECTORY"])
from Processing import ProcessingTask

class DataUploadHandler(tornado.web.RequestHandler):
    def post(self):

api = tornado.web.Application([
    (r"/measurements/upload", DataUploadHandler)

])

if __name__ == "__main__":
    api.listen(4000)
    tornado.ioloop.IOLoop.instance().start()
