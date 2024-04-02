cd /home/appuser
pypy3 createCache.py
gunicorn -k gevent --config gunicorn_config.py main:app
