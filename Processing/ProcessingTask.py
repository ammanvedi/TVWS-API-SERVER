from celery import Celery
from Data_prep import GenerateChannelReadings
from Data_prep import DataToDB

app = Celery('ProcessingTask', broker='amqp://guest@localhost//')

@app.task(name='ProcessingTask.Process')
def Process(inpath, outpath, uid, trackhash):
    generation_result = GenerateChannelReadings.processdata(inpath, outpath, uid, trackhash)
    if generation_result:
        print "INFO (ERROR): Generation was unsuccessful on task" + trackhash + ", will not submit to DB"
    else:
        print "INFO : Generation was successful, passing to Database uploader"
        DataToDB.processToDB(outpath, uid, trackhash)
