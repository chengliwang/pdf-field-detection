#!/bin/bash

/usr/bin/redis-server &
/usr/local/bin/celery -A service.tasks worker -l info &
authbind gunicorn --config python:gunicorn_conf server:app