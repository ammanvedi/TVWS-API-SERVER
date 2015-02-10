from celery import Celery
from Data_prep import GenerateChannelReadings

app = Celery('ProcessingTask', broker='amqp://guest@localhost//')

@app.task(name='processingtask')
def Process(inpath, outpath):
    GenerateChannelReadings.processdata(inpath, outpath)
