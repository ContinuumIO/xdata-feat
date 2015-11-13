#!/bin/sh

source activate bokeh_server
gunicorn -k tornado -w 4 "bokeh.server.start:make_tornado(config_file='config.py')" --log-level=debug --log-file=gunicorn.log --access-logfile=gunicorn_access.log -b 0.0.0.0:5006