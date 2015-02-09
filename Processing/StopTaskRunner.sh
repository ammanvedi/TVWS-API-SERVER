#!/bin/bash
#stop rabbitmq
ps auxww | grep celery | awk '{print $2}' | xargs kill -9
ps auxww | grep celeryd | awk '{print $2}' | xargs kill -9
sudo rabbitmqctl stop
