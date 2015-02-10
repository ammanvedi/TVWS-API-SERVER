from celery import Celery
from Data_prep import GenerateChannelReadings

app = Celery('ProcessingTask', broker='amqp://guest@localhost//')

@app.task
def Process(inpath, outpath):
    GenerateChannelReadings.processdata(inpath, outpath)
