import multiprocessing

bind = "0.0.0.0:443"
workers = multiprocessing.cpu_count() * 2 + 1