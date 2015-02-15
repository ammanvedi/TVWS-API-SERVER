from celery import Celery
from Data_prep import GenerateChannelReadings
from Data_prep import DataToDB

app = Celery('ProcessingTask', broker='amqp://guest@localhost//')

@app.task(name='ProcessingTask.Process')
def Process(inpath, outpath, uid, trackhash):
    GenerateChannelReadings.processdata(inpath, outpath, uid, trackhash)
    DataToDB.processToDB(outpath, uid, trackhash)
