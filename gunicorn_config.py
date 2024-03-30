from config import dvrConfig
import os 

workers = dvrConfig["Server"]["gunicornWorkers"]
threads = dvrConfig["Server"]["gunicornThreads"]
bind = '%s:%s' % (dvrConfig["Server"]["bindAddr"], dvrConfig["Server"]["bindPort"])

if os.environ.get("KUBERNETES_SERVICE_HOST", None) is not None:
    print("Gunicorn running in Kubernetes")
    worker_tmp_dir = "/dev/shm"
    timeout = 600

