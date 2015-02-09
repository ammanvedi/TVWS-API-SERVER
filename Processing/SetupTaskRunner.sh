#!/bin/bash
clear
#save the current working directory
THISDIR=$(pwd)
echo "start rabbitmq"
#start a daemonized rabbitmq (in osx)
# details at http://127.0.0.1:15672/#/connections
sudo rabbitmq-server -detached
#start a daemonized celery (in osx)
#celery -A ProcessingTask worker loglevel=info
celery -A ProcessingTask worker --loglevel=info --concurrency=5 &
