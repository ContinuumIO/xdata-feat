from __future__ import print_function

from random import random, randint
import os
import numpy as np
import pandas as pd
import requests
import datetime as dt
import cols_schema
import time
import urllib
import config
import json
import subprocess as sp
import metrics

ES_ENDPOINT="http://localhost:9200"

cached_spams = {}

def run_fill_missing_security_days():
    import glob
    securities = glob.glob('data/securities/*.csv')
    skip_list = []
    for security in securities:
      print("parsing ", security)
      try:
        fill_missing_security_days(security)
        print("parsed")
      except:
        skip_list.append(security)
        print("error")
    print("skipped list: ", skip_list)


def fill_missing_security_days(security_file):
    f = pd.read_csv(security_file, index_col=0, parse_dates=True)
    dates = f.index
    full_range = pd.date_range(dates[-1], dates[0])
    f = f.reindex(full_range)
    f['Adj Close'].fillna(method='ffill', inplace=True)
    f['Close'].fillna(method='ffill', inplace=True)
    f['Open'].fillna(value=f['Close'], inplace=True)
    f['Volume'].fillna(0, inplace=True)
    f['High'].fillna(value=f['Close'], inplace=True)
    f['Low'].fillna(value=f['Close'], inplace=True)
    # see http://stackoverflow.com/questions/17092671/python-pandas-output-dataframe-to-csv-with-integers
    f['Volume'] = f['Volume'].astype(int) #restore integerness!
    f.index.name = "Date"
    f.sort(ascending=False, inplace=True)
    f.to_csv(security_file, float_format='%g')

def seek_securities(folder):
    secs = set()
    for _file in os.listdir(folder):
        if not _file.startswith("0") and \
            not _file.startswith(".") and \
            _file.endswith('.csv') and not _file.lower().startswith('djia') and \
                os.stat(os.path.join(folder, _file)).st_size != 0:
            secname = _file.replace('.csv', '')
            secs.add(secname)
    return sorted(list(secs))


def load_symbol(symbol, folder, add_std_dev=True):
    base_path = folder + '%s.csv.gz'
    path = base_path % symbol
    df = pd.read_csv(path, compression='gzip', parse_dates={'dt': ['System Date', 'System Time']})
    df = df.sort('dt')
    df['price'] = df['Trade Price']
    df['price_fmt'] = map(str, df['price'])
    df['exch_ts'] = df['Exchange Timestamp']
    df['exch_date'] = df['Session Date']

    df['ind'] = list(range(len(df['dt'])))

    if add_std_dev:
        num_columns = [col for col, type_ in cols_schema.numeric_columns]

        for name in num_columns:
            stdv = df[name].std()
            values = [stdv for x in df.index]
            df['%s_std_dv' % name] = values

    return df

def load_symbol_low_res(symbol, folder, date_range=None):
    if not date_range:
        date_range = config.date_range

    base_path = folder + '%s.csv'
    path = base_path % symbol
    idx = pd.date_range(*date_range)
    df = pd.read_csv(path, parse_dates=['Date'])

    # IMPORTANT! Filter data to the configured range
    df = df[(df['Date'] > date_range[0]) & (df['Date'] < date_range[1])]

    df['dt'] = df['Date']
    df = df.sort('dt')
    df['price'] = df['Adj Close']
    df['price_fmt'] = map(str, df['price'])
    df['Close'] = map(str, df['Close'])
    df['Open'] = map(str, df['Open'])
    df['High'] = map(str, df['High'])
    df['Low'] = map(str, df['Low'])

    df['exch_ts'] = df["dt"].map(lambda x: x.strftime("%Y-%m-%d"))
    df['exch_date'] = df['Date']

    df['ind'] = list(range(len(df['dt'])))

    df['price_delta'] = df.price.diff().shift(-1)/df.price
    df['price_delta'] = df['price_delta'].replace([np.inf, -np.inf], np.nan)
    df['price_delta'].fillna(0, inplace=True)
    df['vol_delta'] = df.Volume.diff().shift(-1)/df.Volume#/df.Volume
    df['vol_delta'] = df['vol_delta'].replace([np.inf, -np.inf], np.nan)
    df['vol_delta'].fillna(0, inplace=True)

    return df

def load_spam(symbol, limit=0):
    if spams_count.get(symbol, 0) == 0:
        return {}

    try:
        url = ES_ENDPOINT + "/untroubled-base6/a/_search?q=s:" + symbol + "&size=900"
        if limit:
            url += "&limit=" + str(limit)
        res = requests.get(url, timeout=4)

        j = res.json()

        if j and j['hits']:
            # import pdb; pdb.set_trace()
            return [x['_source'] for x in j['hits']['hits']]

            return df
    except requests.ConnectionError:
        # TODO: Improve this error handling
        print ("WARNING!! Cannot connect to SPAM SERVICE!")

    except:
        # TODO: REMOVE THIS ASAP IN FAVOR OR A PROPER ERROR LOGGING
        print ("WARNING!! UNKNOW ERROR connecting to SPAM SERVICE!")

    return {}

def load_sec_fillings(symbol, limit=0):
    try:
        url ="http://10.1.93.203:7777/query?s=%s" % symbol

        if limit:
            url += "&limit=" + str(limit)
        res = requests.get(url, timeout=2)

        j = res.json()

        if j and j['results']:
            cols = [u'_id', u'dr', u'dt', u'eml', u'from', u'full_ct', u'mho', u'mip', u'pd_ct', u'qs_ct', u's', u'st',
                    u'st_ct', u'tot_cnt', u'wm', u'wm_ct']
            return j['results']


            return df
    except requests.ConnectionError:
        # TODO: Improve this error handling
        # print ("WARNING!! Cannot connect to SPAM SERVICE!")
        pass

    except:
        # TODO: REMOVE THIS ASAP IN FAVOR OR A PROPER ERROR LOGGING
        # print ("WARNING!! UNKNOW ERROR connecting to SPAM SERVICE!")
        pass

    return {}


def prepare_spam(df, date_range=None):
    global cached_spams
    if len(df):

        if not date_range:
            date_range = config.date_range

        df = pd.DataFrame(df)
        df['sdt'] = pd.to_datetime(df['dt'])

        df = df[(df['sdt'] > date_range[0]) & (df['sdt'] < date_range[1])]

        if not len(df):
            return {}

        df['spam_id'] = df._id

        #TODO: Score should just come out of the service!!!!
        df['score'] = df['pd_ct']

        df['ssec'] = df['s'].apply(lambda x: x.replace(" ", "+"))
        df['wday'] = map(lambda x: x.weekday(), df.sdt)

        try:
            df['date'] = map(lambda x: x.strftime('%Y-%m-%d'), df.sdt)
        except ValueError:
            raise

        df['dt'] = df["sdt"].map(lambda x: dt.datetime(x.year, x.month, x.day))
        df = df.sort('pd_ct')
        gr = df.groupby('dt')

        symbol = df['s'].iloc[0].split(" ")[0]

        for k, content in zip(df['spam_id'], df['content']):
            cached_spams[k.replace('.', '_')] = content

        def aggregator(x):
            if x.name == 'content':
                return ""

            if x.name == 'spam_id':
                return "|||".join(x.tolist())
            if x.name == 'score':
                return len(x.tolist())
            else:
                return x.tolist()[0]


        gdf = pd.DataFrame(gr.agg(aggregator))
        gdf['dt'] = gdf.index
        gdf['sdt'] = pd.to_datetime(gdf['dt'])
        gdf['date'] = map(lambda x: x.strftime('%Y-%m-%d'), gdf.sdt)

        def splitter(txt, content):
            templ = """
    <div>
        <input class="toggle-box" id="header_%(sid)s" type="checkbox">
        <label for="header_%(sid)s" onclick="show_spam('%(sid)s');">%(spam_id)s</label>
        <div class="spam-content" id="content_%(sid)s">%(content)s</div>
    </div>
    """
            out = u""
            for spam_id in txt.split('|||'):
                url = '/spam_details/?symbol=%s&id=%s' % (symbol, spam_id)
                out += templ % {"spam_id": spam_id, 'sid': spam_id.replace('.', '_'),
                                'content': content.replace("\n", "<br>")}

            return out

        gdf['spam_id'] = map(splitter, gdf.spam_id, gdf.content)
        return gdf

    return df

def load_fake_spam(symbol, fakes=10):
    data = {'sdt':[], 'ssec': [], 's': [], 'score': [], 'pd_ct': []}
    for i in range(fakes):
        data['sdt'].append(
            dt.datetime(2014, randint(2, 6), randint(1, 28), randint(0, 23), randint(0, 59))
        )
        data['ssec'].append(symbol)
        data['s'].append(symbol)
        data['score'].append(random())
        data['pd_ct'].append(1)
        data['dt'] = map(lambda x: dt.datetime(x.year, x.month, x.day), data['sdt'])
        data['date'] = map(lambda x: x.strftime('%Y-%m-%d'), data['sdt'])

    return pd.DataFrame(data).sort('score')


def create_hist(evts, max_top=10):
    main_grpd = pd.groupby(evts, by=[evts.index.month]).count()
    main_grpd['i'] = main_grpd.index
    main_grpd['left'] = main_grpd.apply(lambda x: dt.datetime(2014, x.i, 1), axis=1)
    main_grpd['right'] = pd.date_range(
        start=main_grpd['left'][main_grpd.index[0]],
        periods=len(main_grpd),
        freq='M'
    )
    main_grpd['top'] = np.zeros(len(main_grpd.index))
    main_grpd['bottom'] = np.zeros(len(main_grpd.index))
    main_grpd['real_top'] = max_top * main_grpd.sdt/max(main_grpd.sdt)
    return main_grpd


def create_hist_layers(evts, max_top):
    """
    Takes a dataframe of events (where index contains the datetime of each evt
    and return new groupby.count() object with the following columns to build
    an histogram:
        left, right, bottom, top, real_top
    """
    try:
        main_grpd = pd.groupby(evts, by=[evts.index.month]).count()
        main_grpd['i'] = main_grpd.index
        main_grpd['left'] = main_grpd.apply(lambda x: dt.datetime(2014, x.i, 1), axis=1)
        main_grpd['right'] = pd.date_range(
            start=main_grpd['left'][main_grpd.index[0]],
            periods=len(main_grpd),
            freq='M'
        )
        main_grpd['top'] = np.zeros(len(main_grpd.index))
        main_grpd['bottom'] = np.zeros(len(main_grpd.index))
        main_grpd['real_top'] = max_top * main_grpd.sdt/max(main_grpd.sdt)

    except AttributeError:
        # evts is not a DataFrame, most likely case there are no evts
        pass

    for i in range(1, len(evts)+1):
        nevts = evts.iloc[0:i]

        # build a temp dh to compute this layer histogram counts
        tmp= pd.groupby(nevts, by=[nevts.index.month]).count()
        tmp['real_top'] = tmp.sdt/max(tmp.sdt)

        # copy the original df so we have all basic config already set
        grpd = main_grpd.copy()

        for ind in grpd.index:
            grpd.real_top[ind] = tmp.real_top.get(ind, 0)

        yield grpd

def create_hist_data(evts, limit, max_top=10):
    nevts = evts.iloc[0:limit]
    tmp = pd.groupby(nevts, by=[nevts.index.month]).count()
    tmp['real_top'] = max_top * tmp.sdt/max(tmp.sdt)
    res = []

    for i in range(2, 7):
        res.append(tmp['real_top'].get(i, 0))

    return res


def get_stocks_from_topic():
    stocks = set()

    with file('/Users/fpliger/dev/projects/xdata2015/xdata-2015/topic/dump.csv','r') as f:
        for l in f:
            s = l.split(',')[0]
            if s not in stocks:
                stocks.add(s)
                yield s

def download_stocks_from_yahoo():
    u="http://ichart.yahoo.com/table.csv?s=%s&a=0&b=1&c=2010"
    d='/Users/fpliger/dev/projects/xdata2015/xdata-2015/bokeh_app/xapp/data/securities/%s.csv'
    for s in get_stocks_from_topic():
        urllib.urlretrieve(u % s, d % s)



def compute_pump_rank():
    import pumps

    folder = 'data/securities/'

    r = []

    pfounds = {_file.split("_")[1]: _file.split("_")[2].replace(".csv", '') for _file in os.listdir(folder+"cached") if "pumps" in _file}
    for s in seek_securities(folder):
        # import pdb; pdb.set_trace()
        if s in pfounds:
            r.append("%s,%s" % (s, pfounds[s]))

        else:

            try:
                start_dates,  last_quiet_dates,  end_dates, start_prices, last_quiet_prices, end_prices = pumps.find_pumps_easy(
                    s,
                    orig_dir="data/securities",
                    cache_dir="data/securities/cached", min_quiet_days=2
                )
                founds = pd.DataFrame({
                    start_dates: start_dates,  last_quiet_dates: last_quiet_dates,
                    end_dates: end_dates, start_prices: start_prices,
                    last_quiet_prices: start_prices, end_prices: start_prices
                })
                r.append("%s,%i" % (s, len(founds)))
                founds.to_csv("data/securities/cached/pumps_%s_%i.csv" % (s, len(founds)),
                              date_format='%Y-%m-%d')
            except:
                pass

    with file('data/securities/pump_ranks.csv', 'w') as ff:
        ff.write("\n".join((r)))

def get_pumps_rank():
    # ranks = pd.read_csv('data/securities/pump_ranks.csv', names=['symbol', 'rank'])

    ranks = {'symbol': [], 'start_prices': [], 'start': [],'end': [], 'risk_score': [],
     "vol_quotient": [], "rank": [], "end_prices": [], "spam_count": [], "memex_smallcap_scraper_count": []}

    jranks = get_symbols_cached_stats()

    for symbol, cached_attrs in jranks.items():
        ranks['symbol'].append(symbol)
        for attr, values in cached_attrs.items():
            ranks[attr].append(values)

    ranks = pd.DataFrame(ranks)
    return ranks.sort('symbol', ascending=False)

def get_symbols_cached_stats():
    with file('data/securities/cache_pumps_default.json', 'r') as f:
        jranks = json.load(f)

    return jranks

def to_seconds(ts):
    if isinstance(ts, dt.datetime):
        return (ts - dt.datetime(1970, 1, 1)).total_seconds() * 1000
    else:
        return to_seconds(dt.datetime.strptime(ts, '%Y-%m-%d'))

def compute_default_pumps():
    """ Create a new json file (data/securities/cache_pumps_default.json)
    that is the representation of a dict where the keys are the symbole names
    and the values are a tic with the results of the pumps.find_pumps_easy
    method being called with:

                min_quiet_days=3
                growth_tol=1

    """
    import pumps
    folder = 'data/securities/'
    r = {}

    for s in seek_securities(folder):
        if 'quotient_metrics' in s or 'pump_ranks' in s:
            continue

        try:
            intervals = pumps.find_pumps_easy(
                str(s),
                orig_dir="data/securities",
                cache_dir="data/securities/cached",
                min_quiet_days=3,
                growth_tol=1,
                silent=True,
            )

            intervals = pumps.to_dicts(intervals)
            intervals['bottom'] = [0] * len(intervals['start'])
            
            r[s] = intervals
        except:
            pass

    with file('data/securities/cache_pumps_default.json', 'w') as ff:
        json.dump(r, ff)

def compute_all_metrics():

    folder = 'data/securities/'
    r = []

    for s in seek_securities(folder):
        try:
            v, p = metrics.compute_quotient_metrics(
                "data/securities/%s.csv" % s, shift=0
            )
            v = v.replace([np.inf, -np.inf], np.nan)
            v.fillna(0, inplace=True)
            r.append("%s,%s" % (s, v.max()))
        except:
            pass
            # raise

    with file('data/securities/quotient_metrics.csv', 'w') as ff:
        ff.write("\n".join((r)))

def get_quotient_metrics():
    ranks = pd.read_csv('data/securities/quotient_metrics.csv',
                        names=['symbol', 'quotient'])
    return ranks.sort('symbol', ascending=False)

import collections
import json
import functools
from itertools import ifilterfalse

def load_cache(cachefile='data/securities/cached/lru_cache.json'):
    if not os.path.exists(cachefile):
        return {}

    with file(cachefile, 'r') as file_:
        return json.load(file_)

def save_cache(cache, cachefile='data/securities/cached/lru_cache.json'):
    with file(cachefile, 'w') as file_:
        return json.dump(cache, file_)

# from http://code.activestate.com/recipes/498245/
def lru_cache(maxsize=100):
    '''Least-recently-used cache decorator.

    Arguments to the cached function must be hashable.
    Cache performance statistics stored in f.hits and f.misses.
    Clear the cache with f.clear().
    http://en.wikipedia.org/wiki/Cache_algorithms#Least_Recently_Used

    '''
    maxqueue = maxsize * 10
    def decorating_function(user_function,
            len=len, iter=iter, tuple=tuple, sorted=sorted, KeyError=KeyError):
        try:
            cache = {} #load_cache()                  # mapping of args to results
        # yes, it's not nice but we want to really avoid any errors in production
        # just because of the cache
        except:
            cache = {}

        queue = collections.deque() # order that keys have been used
        refcount = collections.Counter()        # times each key is in the queue
        sentinel = "____SENTINEL____" #object()         # marker for looping around the queue
        kwd_mark = "____KWD_MARK____" #object()         # separate positional and keyword args

        # lookup optimizations (ugly but fast)
        queue_append, queue_popleft = queue.append, queue.popleft
        queue_appendleft, queue_pop = queue.appendleft, queue.pop

        @functools.wraps(user_function)
        def wrapper(*args, **kwds):
            # cache key records both positional and keyword args
            key = str(args)
            if kwds:
                key += str((kwd_mark,) + tuple(sorted(kwds.items())))

            # record recent use of this key
            queue_append(key)
            refcount[key] += 1

            # get cache entry or compute if not found
            try:
                result = cache[key]
                wrapper.hits += 1
            except KeyError:
                result = user_function(*args, **kwds)
                cache[key] = result
                wrapper.misses += 1

                # purge least recently used cache entry
                if len(cache) > maxsize:
                    key = queue_popleft()
                    refcount[key] -= 1
                    while refcount[key]:
                        key = queue_popleft()
                        refcount[key] -= 1
                    del cache[key], refcount[key]

            # periodically compact the queue by eliminating duplicate keys
            # while preserving order of most recent access
            if len(queue) > maxqueue:
                refcount.clear()
                queue_appendleft(sentinel)
                for key in ifilterfalse(refcount.__contains__,
                                        iter(queue_pop, sentinel)):
                    queue_appendleft(key)
                    refcount[key] = 1


            return result

        def clear():
            cache.clear()
            queue.clear()
            refcount.clear()
            wrapper.hits = wrapper.misses = 0

        wrapper.hits = wrapper.misses = 0
        wrapper.clear = clear
        return wrapper
    return decorating_function


cached_pumps = {}
with file('data/securities/cache_pumps_default.json', 'r') as ff:
    cached_pumps = json.load(ff)


def load_trends_data(symbol, path='data/trends/monthly_stock_trends.csv', start_date=None):
    trends = pd.read_csv(path)
    trends.index = map(str.upper, trends.pop('symbol'))
    tt = trends.T
    tt.index = pd.to_datetime(tt.index)
    tt['dt'] = tt.index
    if start_date:
        tt = tt[tt['dt'] >= start_date]
    return tt

def get_spams_count(f, sz=25000):
    '''sz is size per shard max to return.  25k is safe
    since there are 25k in collection'''
    d = {   "aggs" : {
                "%ss" % f : {
                    "terms" : { "field" : f, 'size': sz}
                }
            }
        }
    res = sp.Popen(['curl', 
                '-H',
                'Content-Type: application/json', 
                ES_ENDPOINT + '/untroubled-base6/a/_search?size=25000&search_type=count&q=s:*',
                '-d',
                json.dumps(d)
            ],
                stdout=sp.PIPE, 
                stderr=sp.PIPE, 
            ).communicate()

    
    spams = json.loads(res[0])
    r = {v['key'].upper(): v['doc_count'] for v in spams['aggregations']['ss']['buckets']}
    
    return r

def get_spams_count_from_cache():
    with file('../aj/distinct_counts_untroubled-base6.json', 'r') as ff:
        spams_cached = json.load(ff)

    r = {v['key'].upper(): v['doc_count'] for v in spams_cached}

    return r

spams_count = get_spams_count_from_cache()


if __name__=='__main__':
    # compute_pump_rank()
    # compute_all_metrics()
    # compute_default_pumps()
    print(get_spams_count('s'))
