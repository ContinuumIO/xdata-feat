"""
This file demonstrates embedding a bokeh applet into a flask
application. See the README.md file in this dirrectory for
instructions on running.
"""
from __future__ import print_function

import datetime as dt
import logging
logging.basicConfig(level=logging.INFO)

import json

from bokeh.pluginutils import app_document
from flask import Flask, render_template, jsonify, request
import requests
import pumps

from dashboard import TableBoard, StaticDash
import plugins
import utils
from bs4 import BeautifulSoup

from bokeh.embed import components
from bokeh.plotting import figure
from bokeh.resources import Resources#, INLINE
from bokeh.templates import RESOURCES
from bokeh.util.string import encode_utf8

import config
import pandas as pd

ES_ENDPOINT="localhost:9200"

application = Flask('featapp')

# Get custom configuration if any (USE SPECIALLY WHEN SERVING/DEPLOYING
# ON A DIFFERENT PORT AND WITH DIFFERENT GENERAL CONFIGURATIONS )
try:
    with file('gen_config.json', 'r') as gconf_file:
        gen_config = json.load(gconf_file)
except:
    # TODO: We can handle errors in a better way..
    print ("WARNING!!! NO gen_config.json FILE FOUND! USING DEFAULTS:")
    gen_config = dict(
        bokeh_url="http://127.0.0.1:5006",
        applet_url="http://127.0.0.1:5050",
        host='0.0.0.0',
        port=5050,
        debug=True,
    )
    print (gen_config)

@app_document("FEAT", gen_config['bokeh_url'])
def make_feat_applet():
    symbol = request.args.get('symbol', '')

    if symbol:
        app = Dashboard.create(symbol=symbol)
    else:
        app = TableBoard.create(symbol=symbol)
    return app

@application.route("/")
def newapplet():
    symbol = request.args.get('symbol', '')

    INLINE = Resources(mode="inline", minified=False,)

    if symbol:
        templname = "feat_static.html"
    else:
        symbol = 'HEMP'
        templname = "feat_home.html"

    app = StaticDash.create(symbol)
    plot_resources = RESOURCES.render(
        js_raw=INLINE.js_raw,
        css_raw=INLINE.css_raw,
        js_files=INLINE.js_files,
        css_files=INLINE.css_files,
    )

    plot_script, extra_divs = components(
        {
            "table_ranks": app.table_stocks_rank,
            "main_app": app.children[0],
            "btn_detect_pumps": app.btn_detect_pumps,
            "dlg_peaks": app.PEAKS,
        },
        INLINE
    )

    def get_id(div):
        soup = BeautifulSoup(div)
        tag=soup.div
        return soup.div.get('id')

    div_ids = {k: get_id(v) for k, v in extra_divs.items()}
    return render_template(
        templname,
        app_url = gen_config['bokeh_url'] + "/bokeh/jsgenerate/VBox/Dashboard/Dashboard",
        symbol = symbol,
        extra_divs = extra_divs,
        plot_script = plot_script,
        plot_resources=plot_resources,
        bokeh_divs_id_json = json.dumps(div_ids),
        bokeh_divs_id = div_ids
    )


@application.route("/tour/")
def tour():
    return render_template(
        "feat_tour.html"
    )


@application.route("/bokeh/peaks/", methods=['GET', 'OPTIONS'])
def serve_peaks():
    args = request.args
    start_dates,  last_quiet_dates,  end_dates, start_prices, last_quiet_prices, end_prices = pumps.find_pumps_easy(
        request.args['s'],
        orig_dir="data/securities",
        cache_dir="data/securities/cached",
        min_quiet_days=int(args['min_quiet_days']),
        quiet_tol=float(args['quiet_tol'] if '.' in args['quiet_tol'] else args['quiet_tol'] + '.'),
        min_growth_days=int(args['min_growth_days']),
        max_growth_days=int(args['max_growth_days']),
        growth_tol=float(args['growth_tol'] if '.' in args['growth_tol'] else args['growth_tol'] + '.'),
        silent=True,
    )

    conv = lambda x: utils.to_seconds(pd.to_datetime(x))
    res = {
        'results': sorted(
            [{'start': s, 'end':  e}
             for s, e in zip(
                sorted(map(utils.to_seconds, start_dates)), 
                sorted(map(utils.to_seconds, end_dates)))
             if s and s > conv(config.date_range[0]) and s < conv(config.date_range[1])
             ]
        )
    }
    
    return jsonify(res)


@application.route("/edgar-base15/num/_search/", methods=['GET', 'OPTIONS'])
def edgar_num():
    args = request.args
    url = ES_ENDPOINT + "/edgar-base15/num/_search?" + request.query_string
    res = requests.get(url, timeout=2)

    return jsonify(res.json())


@application.route("/spam_details/")
def spam_details():
    spam_id = request.args['id']
    return jsonify({"content": utils.cached_spams[spam_id]})
    symbol = request.args['symbol']
    url = "http://10.1.93.203:7777/raw-email?em=%s" % spam_id
    res = requests.get(url, timeout=2)
    content = res.json()['content'].replace('\n', '<br>')
    return render_template(
            "spam_mail.html",
            content = content,
            spam_id = spam_id,
            symbol = request.args['symbol']
        )


if __name__ == "__main__":
    print("\nView this example at: %s\n" % gen_config['applet_url'])
    application.debug = gen_config['debug']
    application.run(host=gen_config['host'], port=gen_config['port'])
