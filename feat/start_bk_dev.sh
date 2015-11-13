#!/bin/sh

source activate bokeh_server
bokeh-server --script dashboard.py --port 5007 --ip 0.0.0.0