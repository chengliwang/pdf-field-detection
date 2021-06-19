import multiprocessing, os

bind = "0.0.0.0:80"
port = os.getenv('PORT')
if port != None:
    bind = "0.0.0.0:" + port
workers = multiprocessing.cpu_count() * 2 + 1