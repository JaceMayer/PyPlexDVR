cd /home/appuser
python3.12 createCache.py
gunicorn -k gevent --config gunicorn_config.py main:app
