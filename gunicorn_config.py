from config import dvrConfig
workers = dvrConfig["Server"]["gunicornWorkers"]
threads = dvrConfig["Server"]["gunicornThreads"]
bind = '%s:%s' % (dvrConfig["Server"]["bindAddr"], dvrConfig["Server"]["bindPort"])
