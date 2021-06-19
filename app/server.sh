#!/bin/bash

/usr/bin/redis-server &
/usr/local/bin/celery -A service.tasks worker -l info &
gunicorn --config python:gunicorn_conf server:app