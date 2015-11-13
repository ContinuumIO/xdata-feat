from __future__ import print_function

from collections import OrderedDict
import requests
import pandas as pd
import numpy as np
import datetime as dt
from bokeh.models.actions import Callback
from bokeh.models.glyphs import Circle, Diamond, Text, CircleX
from bokeh.models.sources import ColumnDataSource
from bokeh.models.widgets import (TableColumn, NumberEditor, DataTable, Panel,
                                  Button, TextInput, Dialog, Slider, Paragraph)
from bokeh.models import HoverTool

from bokeh.io import vplot

from flask import request, jsonify
from bokeh.server.crossdomain import crossdomain

ES_ENDPOINT="http://localhost:9200"

HOVER_CB_TEMPL = """
    if (cb_data.index['1d'].indices.length > 0){
        msg = {
            activity: 'inspect',
            action: 'mouseover',
            elementType: 'canvas',
            elementId: '%s',
            elementGroup: 'chart_group',
            source: 'user',
            tags: ['query']
        };
        ale.log(msg);
    }
"""

class EventsFinder(object):
    # name of the widget that will be created to let user select this
    # type of events
    name = ""
    widget_name = ""
    widget_title = ""
    callback_code = ""
    widget_defaults = dict(value=0, start=0, step=1)
    url = ''

    cb_code_templ = """
        msg = {
            activity: 'alter',
            action: 'slide',
            elementType: 'slider',
            elementId: "%(widget_name)s",
            elementGroup: 'input_group',
            source: 'user',
            tags: ['query']
        };
        ale.log(msg);

        // url = "/bokeh/%(name)s/?limit=" + %(widget_name)s.get('value');
        url = "%(url)s?s=%(symbol)s";
        xhr = $.ajax({
            type: 'GET',
            url: url,
            contentType: "application/json",
            // data: jsondata,
            header: {
              client: "javascript"
            }
        });

        xhr.done(function(data) {
            hist_source.get('data').top = data.values;
            hist_source.trigger('change');
        });

        var new_selection = [];
        for (var i = 0; i < %(widget_name)s.get('value'); i++) {
            new_selection.push(i);
        }
        window.new_selection_object = {
            '0d': {'flag': false, 'indices': []},
            '1d': {'indices': new_selection},
            '2d': {'indices': []}
        };

        evts_source.attributes.selected = window.new_selection_object;
        evts_source.trigger('change');
    """

    evts_selection_cb_templ = """
        if (evts_source.get('selected') && evts_source.get('selected')['1d'].indices.length == 1){
            window.last_selected_spam_index = evts_source.get('selected')['1d'].indices[0];
            window.last_evt_index = evts_source.get('selected')['1d'].indices[0];
            dat = evts_source.get('data');
            window.last_selected_dt = dat.dt[evts_source.get('selected')['1d'].indices[0]];
        }
    """

    def __init__(self, symbol, max_values, app):
        self.app = app
        self.symbol = symbol
        self.evts = {}
        self.evts_grpd = {}
        self.evts_source = ColumnDataSource()
        self.hist_source = ColumnDataSource()
        self.layers = OrderedDict()
        self.search(symbol, max_values)

        global services
        services[self.name] = self


    @classmethod
    def register_endpoint(cls):
        raise NotImplementedError()

    def create_objects(self):
        d = {}
        elems = [
            ('%s', self.widget),
            ('%s_source', self.evts_source),
            ('h%s_source', self.hist_source),
            ('%s_tab', Panel(title=self.name)),
            ('%s_table', self.table),
        ]
        for templ, el in elems:
            d[templ % self.name] = el

        return d

    def search(self):
        raise NotImplementedError()

    @property
    def widget(self):
        # select all spam events
        self.evts_source.selected = {
            '0d': {'flag': False, 'indices': []},
            '1d': {'indices': range(len(self.evts))},
            '2d': {'indices': []}
        }

        names = dict(
            js_list_of_sources=str(list(self.layers.keys())).replace("'", ""),
            widget_name=self.widget_name, url=self.url,
            name=self.name, symbol=self.symbol,
        )
        code = self.cb_code_templ % names
        objs = dict(
            evts_source=self.evts_source,
            hist_source=self.hist_source,
        )
        objs.update(self.layers)

        callback = Callback(args=objs, code=code)
        kws = dict(self.widget_defaults)
        kws['value']=len(self.evts)
        slider = Slider(
            title = "%s (total events: %i)" % (self.name.capitalize(), len(self.evts)),
            end = len(self.evts), callback=callback, **kws)
        callback.args[self.widget_name] = slider

        code = self.evts_selection_cb_templ % names
        objs = {'evts_source': self.evts_source, self.widget_name: slider}
        callback = Callback(args=objs, code=code)
        self.evts_source.callback = callback

        return slider

    @property
    def table(self):
        table = DataTable(source=self.evts_source, width=1200, height=800)
        if len(self.evts):
            table.columns = [
                TableColumn(field=x, title=x, editor=NumberEditor())
                for x in self.evts.columns
            ]
        return table

    def add_glyph_to_plot(self, plot, hover_tool=False, evts_source=None):
        if evts_source is None:
            evts_source = self.evts_source

        glyph = Circle(x='dt', y='mapped_score',
                  fill_color='red', line_color=None, size=10,
                  fill_alpha=0.6)
        empty_glyph = Circle(x='dt', y='mapped_score',
                      fill_color='red', line_color=None, size=10,
                      fill_alpha=0.6)

        evts_renderer = plot.add_glyph(
            evts_source, glyph,
            selection_glyph=glyph,
            nonselection_glyph=empty_glyph
        )

        # set source tag so it can be found on JS side to be enabled/disabled by legend
        self.evts_source.tags = [self.name]

        return evts_renderer


class SpamFinder(EventsFinder):
    widget_name = 'spam_slider'
    name = 'spam'
    url = "http://10.1.93.203:7777/query"

    def cb_code(self, symbol):
        url = "http://www.otcmarkets.com/stock/%s/news" % symbol
        url_yf_1 = "http://finance.yahoo.com/q/h?s=%s&t=" % symbol
        url_yf_2 = "T23:59:59-4:00"

        code = """
            var clicked_elements = [];
            var date = undefined;
            var dat = spam_source.get('data');
            var sec_data = sec_source.get('data');
            // var forum_data = forum_source.get('data');
            var memex_data = memex_forum_source.get('data');
            var small_cap_news_data = small_cap_news_source.get('data');

            //var spamdate = dat.date[window.last_selected_spam_index];
            //var spams_count = dat.score[window.last_selected_spam_index];
            //var spam_mails = dat.spam_id[window.last_selected_spam_index];


            var small_cap_news = [];
            if (small_cap_news_data.dt != undefined){
                for (var i = 0; i < small_cap_news_data.dt.length; i++) {
                    if (window.last_selected_dt == small_cap_news_data.dt[i]){
                        small_cap_news.push(i);
                        date = small_cap_news_data.date[i];
                        clicked_elements.push('small_cap_news');
                    }
                }
            }

            var forums = [];
            //if (forum_data.dt != undefined){
            //    for (var i = 0; i < forum_data.dt.length; i++) {
            //        if (window.last_selected_dt == forum_data.dt[i]){
            //            forums.push(i);
            //            date = forum_data.date[i];
            //        }
            //    }
            //}


            var memex = [];
            if (memex_data.dt != undefined){
                for (var i = 0; i < memex_data.dt.length; i++) {
                    if (window.last_selected_dt == memex_data.dt[i]){
                        memex.push(i);
                        date = memex_data.date[i];
                        clicked_elements.push('memex_forum');
                    }
                }
            }

            var spams = [];
            if (dat.dt != undefined){
                for (var i = 0; i < dat.dt.length; i++) {
                    if (window.last_selected_dt == dat.dt[i]){
                        spams.push(i);
                        date = dat.date[i];
                        clicked_elements.push('spam');
                    }
                }
            }

            var secs = [];
            if (sec_data.dt != undefined){
                for (var i = 0; i < sec_data.dt.length; i++) {
                    if (window.last_selected_dt == sec_data.dt[i]){
                        secs.push(i);
                        date = sec_data.date[i];
                        clicked_elements.push('edgar');
                    }
                }
            }

            html_txt = '<div><p>You have selected: ' + date + '.<\p>';

            if (spams.length > 0){
                var spam_mails = dat.spam_id[window.last_selected_spam_index];
                html_txt = html_txt + '<p>Spam found in the selected day: ' + spams.length + '.<\p> \
                <p>Spam details (click on the email id to open the spam email):<\p> ' + spam_mails;
            }else{
                html_txt = html_txt + '<p>No Spam found in the selected day<\p>';
            }

            //if (forums.length > 0){
            //    html_txt = html_txt + '<p>Forum data found in the selected day:' + forums.length + '.<\p> \
            //    <p>Forum data details (click on the id to open the page content):<\p> ' + forum_data.content[forums[0]] ;
            //}else{
            //    html_txt = html_txt + '<p>Forum data found in the selected day: ' + forums.length + '.<\p>';
            //}

            if (memex.length > 0){
                html_txt = html_txt + '<p>Memex financial forum data found in the selected day:' + memex.length + '.<\p> \
                <p>Memex data details (click on the id to open the page content):<\p> ' + memex_data.content[memex[0]] ;
            }else{
                html_txt = html_txt + '<p>No Memex financial forum data found in the selected day<\p>';
            }

            if (secs.length > 0){
                html_txt = html_txt + '<p>SEC EDGAR filings found in the selected day:' + secs.length + '.<\p> \
                <p>EDGAR data details (click on the id to open the page content):<\p> ' + sec_data.content[secs[0]] ;
            }else{
                html_txt = html_txt + '<p>No SEC EDGAR filings found in the selected day<\p>';
            }

            if (small_cap_news.length > 0){
                html_txt = html_txt + '<p>Small Cap News found in the selected day:' + small_cap_news.length + '.<\p> \
                <p>Small Cap News details (click on the id to open the page content):<\p> ' + small_cap_news_data.content[small_cap_news[0]] ;
            }else{
                html_txt = html_txt + '<p>No Small Cap News found in the selected day<\p>';
            }

            for (var i = 0; i < clicked_elements.length; i++) {
                var clicked_el = clicked_elements[i];
                msg = {
                    activity: 'perform',
                    action: 'click',
                    elementType: 'canvas',
                    elementId: plot.get('tags')[0],
                    elementSub: clicked_el,
                    elementGroup: 'chart_group',
                    source: 'user',
                    tags: ['query', 'Date, ' + date]
                    //meta: 'Date, ' + date
                };
                console.log(msg);
                ale.log(msg);
            }

            if (small_cap_news.length > 0 || spams.length > 0 || forums.length > 0 || secs.length > 0 || memex.length > 0){
                html_txt = html_txt + '</div>';
                $("#info_dialog_content").html(html_txt);

                $("#info_dialog").addClass('modalTarget');

                  // Info dialog opening
                    var msg = {
                        activity: 'open',
                        action: 'show',
                        elementId: 'tapToolInfoDialog',
                        elementType: 'dialog_box',
                        elementSub: 'panel',
                        elementGroup: 'query_group',
                        source: 'system',
                        tags: ['panelInfo, ' + date]
                        //meta: 'panelInfo, ' + date
                    };
                    console.log(msg);
                    ale.log(msg);
                    window.last_selected_dt = undefined;

                function reset_spams() {
                    spam_source.set('selected', window.new_selection_object);
                }
                setTimeout(reset_spams, 1000);
            }

        """
        return code

    @classmethod
    def register_endpoint(cls, app):
        @app.route("/bokeh/%s/" % cls.name, methods=['GET', 'OPTIONS'])
        @crossdomain(origin="*", methods=['GET', 'POST'], headers=None)
        def serve_spams():
            from utils import create_hist_data
            limit = int(request.args['limit'])
            serv = services[cls.name]
            return jsonify(values=create_hist_data(serv.evts, limit))

    def search(self, symbol, max_values):
        # SPAM
        from utils import load_spam, prepare_spam, create_hist
        try:
            self.evts = spams = prepare_spam(
                load_spam(symbol) or {},
                (min(self.app._df['dt']), max(self.app._df['dt']))
            )
        except IndexError:
            self.evts = spams = {}
        except:
            #TODO: there should be much better error handling here
            self.evts = spams = {}

        slen = len(spams)
        source_data = dict()
        mapped_score = []

        if slen:
            spams.index = spams.sdt
            source_data['sdt'] = list(spams.sdt)
            source_data['pd_ct'] = source_data['score'] = list(spams.score)
            source_data['s'] = list(spams.s)
            source_data['ssec'] = list(spams.ssec)

            # _max = max(self.app.source.data['price'])
            data = self.app.source.data
            pmap = {d: p for d, p in zip(data['dt'], data['price'])}
            mapped_score = []
            prev = 0
            default = data['price'].mean()
            for lrdt in spams.dt:
                new = pmap.get(lrdt, default)
                mapped_score.append(new)
                prev = new

            self.evts_grpd = create_hist(spams)
        else:
            self.evts_grpd = {k:[] for k in ['i', 'left', 'right', 'top', 'bottom', 'real_top']}

        self.evts_source = ColumnDataSource(spams if spams is not None else {})
        self.evts_source.add(list(mapped_score), 'mapped_score')
        self.hist_source = ColumnDataSource(self.evts_grpd)


class SECFillingsFinder(EventsFinder):
    widget_name = 'sec_slider'
    name = 'sec'
    url = ES_ENDPOINT + "/edgar-base25/sub/_search?q=instance:%%22%(symbol)s%%22"

    def cb_code(self, symbol):
        return ""

    def load_data(self, symbol, limit=0):
        try:
            url = self.url % {"symbol": symbol}
            res = requests.get(url, timeout=4)

            j = res.json()

            if j and j['hits']:
                recs = []
                for x in j['hits']['hits']:
                    rec = x['_source']
                    rec.update(self.get_adsh(rec['adsh']))
                    recs.append(rec)
                return recs

        except requests.ConnectionError:
            # TODO: Improve this error handling
            print ("WARNING!! Cannot connect to EDGAR SERVICE!")

        except:
            # TODO: REMOVE THIS ASAP IN FAVOR OR A PROPER ERROR LOGGING
            print ("WARNING!! UNKNOW ERROR connecting to EDGAR SERVICE!")

        return {}

    def prepare_data(self, df, date_range):
        if len(df):
            df = pd.DataFrame(df)
            df['dt'] = pd.to_datetime(df['accepted'])
            df = df[(df['dt'] > date_range[0]) & (df['dt'] < date_range[1])]

            if not len(df):
                return {}

            data = self.app.source.data
            # df['mapped_score'] = [max(data['price']) / 2.] * len(df['dt'])
            pmap = {d.date(): p for d, p in zip(data['dt'], data['price'])}
            mapped_score = []
            default = data['price'].mean()
            min_, max_ = min(data['price']), max(data['price'])
            for lrdt in df.dt:
                new = pmap.get(lrdt.date(), default)
                # print (lrdt, pmap[0])
                if new < default:
                    new += new * 0.05
                    new = min(new, max_)
                else:
                    new -= new * 0.05
                    new = max(new, min_)
                mapped_score.append(new)

            df['mapped_score'] = mapped_score
            df['date'] = map(lambda x: x.strftime('%Y-%m-%d'), df.dt)


            def splitter(adsh, tag, accepted, uom, value, version,
                         filled_dt, form, name, former):
                templ = """
        <div>
            <input class="toggle-box" id="header_%(sid)s" type="checkbox" >
            <label for="header_%(sid)s" onclick="log_expand_element('EDGAR', '%(sid)s');">%(spam_id)s</label>
            <div class="spam-content">
                <p> ADSH: %(adsh)s</p>
                <p> Form: %(form)s</p>
                <p> Filed at: %(filled_dt)s</p>
                <p> Accepted: %(accepted)s</p>
                <p> Tag: %(tag)s</p>
                <p> Uom: %(uom)s</p>
                <p> Value: %(value)s</p>
                <p> Version: %(version)s</p>
                <p> Name: %(name)s</p>
                <p> Former: %(former)s</p>
            </div>
        </div>
        """
                vars = locals()
                vars.update({"spam_id": adsh, 'sid': adsh.replace('.', '_').replace('/', '_')})
                return templ % vars

            df['content'] = map(splitter, df.adsh, df.tag, df.accepted, df.uom, df.value,
                                df.version, df.filed_dt, df.form, df.name, df.former)

            df['lbl'] = ["E"] * len(df['dt'])
            df = df.sort('dt')

        return df

    def get_adsh(self, adsh):
        query_string = "q=adsh:%s" % adsh
        args = request.args
        url = ES_ENDPOINT + "/edgar-base15/num/_search?" + query_string
        res = requests.get(url, timeout=2)
        jj = res.json()

        details = jj['hits']['hits'][0]['_source']
        return details

    def search(self, symbol, date_range):
        self.evts = self.prepare_data(
            self.load_data(symbol),
            (min(self.app._df['dt']), max(self.app._df['dt']))
        )

        self.evts_source = ColumnDataSource(self.evts if len(self.evts) else {})

        names = dict(
            js_list_of_sources=str(list(self.layers.keys())).replace("'", ""),
            widget_name=self.widget_name, url=self.url,
            name=self.name, symbol=self.symbol,
        )

        code = self.evts_selection_cb_templ % names
        objs = {'evts_source': self.evts_source}
        callback = Callback(args=objs, code=code)
        self.evts_source.callback = callback

    def add_glyph_to_plot(self, plot, hover_tool=False, evts_source=None):
        if evts_source is None:
            evts_source = self.evts_source

        glyph = Diamond(x='dt', y='mapped_score', fill_color='blue',
                    line_color=None, size=22, fill_alpha=0.6)
        empty_glyph = Diamond(x='dt', y='mapped_score', fill_color='blue',
                          line_color=None, size=22, fill_alpha=0.6)

        evts_renderer = plot.add_glyph(
            evts_source, empty_glyph,
            selection_glyph=glyph,
            nonselection_glyph=empty_glyph
        )

        text = Text(
            x='dt', y='mapped_score', text='lbl', text_font_size='6pt',
            text_color='white', x_offset=-3, y_offset=5)
        plot.add_glyph(evts_source, text)

        # set source tag so it can be found on JS side to be enabled/disabled by legend
        self.evts_source.tags = ['edgar']

        if hover_tool:
            hover = HoverTool(renderers=[evts_renderer])
            hover.tooltips =  """
            <div class="split-tooltip">
                <h3>SEC EDGAR filings</h3>
                <table><tbody>
                    <tr><td>Accepted on:</td><td> @accepted</td></tr>
                    <tr><td>ADSH:</td><td> @adsh</td></tr>
                    <tr><td>Tag:</td><td> @tag</td></tr>
                    <tr><td>Uom:</td><td> @uom</td></tr>
                    <tr><td>Value:</td><td> @value</td></tr>
                    <tr><td>Version:</td><td> @version</td></tr>
                </table></tbody>
            </div>
            """
            hover.callback = Callback(code=HOVER_CB_TEMPL % "sec_edgar_glyph")
            plot.add_tools(hover)

        return evts_renderer

class ForumDataFinder(EventsFinder):
    widget_name = 'forum_slider'
    name = 'forum'
    url = ES_ENDPOINT + "/financial-forum6/a/_search?q=s:%%22%(symbol)s%%22"

    def cb_code(self, symbol):
        return ""

    def load_data(self, symbol, limit=0):
        try:
            url = self.url % {"symbol": symbol}
            res = requests.get(url, timeout=4)

            j = res.json()

            if j and j['hits']:
                recs = []
                for x in j['hits']['hits']:
                    rec = x['_source']
                    recs.append(rec)
                return recs

        except requests.ConnectionError:
            # TODO: Improve this error handling
            print ("WARNING!! Cannot connect to SPAM SERVICE!")

        except:
            # TODO: REMOVE THIS ASAP IN FAVOR OR A PROPER ERROR LOGGING
            print ("WARNING!! UNKNOW ERROR connecting to SPAM SERVICE!")

        return {}

    def prepare_data(self, df, date_range):
        if len(df):
            df = pd.DataFrame(df)
            df['dt'] = pd.to_datetime(df['timestamp'])
            df = df[(df['dt'] > date_range[0]) & (df['dt'] < date_range[1])]

            if not len(df):
                return {}

            df = df[['dt', 'timestamp', 's', 'link_txt', 'crawlid', 'url']]

            data = self.app.source.data
            # df['mapped_score'] = [max(data['price']) / 2.] * len(df['dt'])
            pmap = {d.date(): p for d, p in zip(data['dt'], data['price'])}
            mapped_score = []
            default = data['price'].mean()
            min_, max_ = min(data['price']), max(data['price'])
            for lrdt in df.dt:
                new = pmap.get(lrdt.date(), default)
                # print (lrdt, pmap[0])
                if new < default:
                    new += new * 0.05
                    new = min(new, max_)
                else:
                    new -= new * 0.05
                    new = max(new, min_)
                mapped_score.append(new)

            df['mapped_score'] = mapped_score

            df['lbl'] = ["F"] * len(df['dt'])
            df = df.sort('dt')


            df['dt'] = df["dt"].map(lambda x: dt.datetime(x.year, x.month, x.day))
            gr = df.groupby('dt')

            symbol = df['s'].iloc[0].split(" ")[0]

            def aggregator(x):
                if x.name == 'link_txt' or x.name == 'crawlid':
                    return "|||".join(x.tolist())
                else:
                    return x.tolist()[0]


            gdf = pd.DataFrame(gr.agg(aggregator))
            gdf['dt'] = gdf.index
            gdf['date'] = map(lambda x: x.strftime('%Y-%m-%d'), gdf.dt)

            def splitter(txt, content):
                templ = """
        <div>
            <input class="toggle-box" id="header_%(sid)s" type="checkbox" >
            <label for="header_%(sid)s"  onclick="log_expand_element('Forum', '%(sid)s');">%(spam_id)s</label>
            <div class="spam-content">%(content)s</div>
        </div>
        """

                out = u""
                for _id in txt.split('|||'):
                    out += templ % {"spam_id": _id, 'sid': _id.replace('.', '_').replace('/', '_'),
                                    'content': content.replace("\n", "<br>")}

                return out

            gdf['content'] = map(splitter, gdf.crawlid, gdf.link_txt)
            return gdf

        return df

    def search(self, symbol, date_range):
        self.evts = self.prepare_data(
            self.load_data(symbol),
            (min(self.app._df['dt']), max(self.app._df['dt']))
        )

        self.evts_source = ColumnDataSource(self.evts if len(self.evts) else {})

        names = dict(
            js_list_of_sources=str(list(self.layers.keys())).replace("'", ""),
            widget_name=self.widget_name, url=self.url,
            name=self.name, symbol=self.symbol,
        )

        code = self.evts_selection_cb_templ % names
        objs = {'evts_source': self.evts_source}
        callback = Callback(args=objs, code=code)
        self.evts_source.callback = callback


    def add_glyph_to_plot(self, plot, hover_tool=False, evts_source=None):
        if evts_source is None:
            evts_source = self.evts_source

        glyph = CircleX(x='dt', y='mapped_score', fill_color='blue',
                    line_color=None, size=22, fill_alpha=0.6)
        empty_glyph = CircleX(x='dt', y='mapped_score', fill_color='blue',
                          line_color=None, size=22, fill_alpha=0.6)

        evts_renderer = plot.add_glyph(
            evts_source, empty_glyph,
            selection_glyph=glyph,
            nonselection_glyph=empty_glyph
        )
        # text_source = ColumnDataSource(data)
        text = Text(
            x='dt', y='mapped_score', text='lbl', text_font_size='6pt',
            text_color='white', x_offset=-3, y_offset=5)
        plot.add_glyph(evts_source, text)

        if hover_tool:

            hover = HoverTool(renderers=[evts_renderer])
            hover.tooltips =  """
            <div class="split-tooltip">
                <h3>Forum Data</h3>
                <table><tbody>
                    <tr><td>Post created on:</td><td> @timestamp</td></tr>
                    <tr><td>Url:</td><td> @url</td></tr>
                </table></tbody>
            </div>
            """
            hover.callback = Callback(code=HOVER_CB_TEMPL % "forum_glyph")
            plot.add_tools(hover)

        return evts_renderer


class MemexForumDataFinder(ForumDataFinder):
    widget_name = 'memex_forum_slider'
    name = 'memex_forum'
    url = ES_ENDPOINT + "/memex-smallcap-scraper6/a/_search?q=stock:%%22%(symbol)s%%22&size=1000"


    def prepare_data(self, df, date_range):
        if len(df):
            df = pd.DataFrame(df)
            df['timestamp'] = df['dt']
            df['dt'] = pd.to_datetime(df['timestamp'])
            df = df[(df['dt'] > date_range[0]) & (df['dt'] < date_range[1])]

            if not len(df):
                return {}

            df['link_txt'] = df['content']
            df['crawlid'] = df['_id']
            df['s'] = df['stock']
            df['user'] = df['author']
            df['replyTo'] = df['author']

            data = self.app.source.data
            pmap = {d.date(): p for d, p in zip(data['dt'], data['price'])}
            mapped_score = []
            default = data['price'].mean()
            min_, max_ = min(data['price']), max(data['price'])
            for lrdt in df.dt:
                new = pmap.get(lrdt.date(), default)
                if new < default:
                    new += new * 0.05
                    new = min(new, max_)
                else:
                    new -= new * 0.05
                    new = max(new, min_)
                mapped_score.append(new)

            df['mapped_score'] = mapped_score

            df['lbl'] = ["M"] * len(df['dt'])
            df = df.sort('dt')


            df['dt'] = df["dt"].map(lambda x: dt.datetime(x.year, x.month, x.day))
            gr = df.groupby('dt')

            symbol = df['s'].iloc[0].split(" ")[0]

            def aggregator(x):
                if x.name == 'link_txt' or x.name == 'crawlid' or x.name == 'content':
                    return "|||".join(x.tolist())
                # if x.name == 'mapped_score':
                #     return len(x.tolist())
                else:
                    return x.tolist()[0]


            gdf = pd.DataFrame(gr.agg(aggregator))
            gdf['dt'] = gdf.index
            gdf['date'] = map(lambda x: x.strftime('%Y-%m-%d'), gdf.dt)

            def splitter(txt, content, user, replyTo, title, timestamp, full_url):
                templ = """
        <div>
            <input class="toggle-box" id="header_%(sid)s" type="checkbox" >
            <label for="header_%(sid)s" onclick="log_expand_element('MemexForum', '%(sid)s');">%(title)s - (%(spam_id)s)</label>
            <div class="spam-content">
                <p> User: %(user)s</p>
                <p> Timestamp: %(timestamp)s</p>
                <p> Content: %(content)s</p>
                <p> Full url: <a target="_blank" href="%(full_url)s">%(full_url)s</a></p>
            </div>
        </div>
        """
                out = u""
                for _id in txt.split('|||'):
                    out += templ % {"spam_id": _id, 'sid': _id.replace('.', '_').replace('/', '_'),
                                    'content': content.replace("\n", "<br>"),
                                    "user": user, "replyTo": replyTo,'full_url': full_url,
                                    "title": title, "timestamp": timestamp}

                return out

            gdf['content'] = map(splitter, gdf.crawlid, gdf.link_txt, gdf.user,
                                 gdf.replyTo, gdf.title, gdf.timestamp, gdf.full_url)
            return gdf

        return df



    def add_glyph_to_plot(self, plot, hover_tool=False, evts_source=None):
        if evts_source is None:
            evts_source = self.evts_source

        glyph = CircleX(x='dt', y='mapped_score', fill_color='orange',
                    line_color=None, size=13, fill_alpha=0.6)
        empty_glyph = CircleX(x='dt', y='mapped_score', fill_color='orange',
                          line_color=None, size=13, fill_alpha=0.6)

        evts_renderer = plot.add_glyph(
            evts_source, empty_glyph,
            selection_glyph=glyph,
            nonselection_glyph=empty_glyph
        )
        # text_source = ColumnDataSource(data)
        # text = Text(
        #     x='dt', y='mapped_score', text='lbl', text_font_size='6pt',
        #     text_color='white', x_offset=-3, y_offset=5)
        # plot.add_glyph(evts_source, text)

        if hover_tool:
            hover = HoverTool(renderers=[evts_renderer])
            hover.tooltips =  """
            <div class="split-tooltip">
                <h3>MEMEX Forum Data</h3>
                <table><tbody>
                    <tr><td>Created on:</td><td> @timestamp</td></tr>
                    <tr><td>By:</td><td> @user</td></tr>
                    <tr><td>On reply to:</td><td> @title</td></tr>
                </table></tbody>
            </div>
            """
            hover.callback = Callback(code=HOVER_CB_TEMPL % "memex_forum_glyph")
            plot.add_tools(hover)

        self.evts_source.tags = ['memex_forum']

        return evts_renderer


class SmallCapNews(ForumDataFinder):
    widget_name = 'small_cap_news_slider'
    name = 'small_cap_news'
    # url = ES_ENDPOINT + "/small-cap-news3/a/_search?q=size:1000&s:%%22%(symbol)s%%22"
    url = ES_ENDPOINT + "/small-cap-news4/a/_search?q=s:%(symbol)s&size=1000"

    def prepare_data(self, df, date_range):
        _df = df
        if len(df):
            df = pd.DataFrame(df)
            df['timestamp'] = df['dt']

            df['dt'] = pd.to_datetime(df['timestamp'])
            df = df[(df['dt'] > date_range[0]) & (df['dt'] < date_range[1])]

            if not len(df):
                return {}

            # df['link_txt'] = df['title']
            df['crawlid'] = df['_id']
            # df['s'] = df['stock']

            data = self.app.source.data
            pmap = {d.date(): p for d, p in zip(data['dt'], data['price'])}
            mapped_score = []
            default = data['price'].mean()
            min_, max_ = min(data['price']), max(data['price'])
            for lrdt in df.dt:
                new = pmap.get(lrdt.date(), default)
                if new < default:
                    new += new * 0.05
                    new = min(new, max_)
                else:
                    new -= new * 0.05
                    new = max(new, min_)
                mapped_score.append(new)

            df['mapped_score'] = mapped_score

            df['lbl'] = ["S"] * len(df['dt'])
            df = df.sort('dt')


            df['dt'] = df["dt"].map(lambda x: dt.datetime(x.year, x.month, x.day))
            gr = df.groupby('dt')

            symbol = df['s'].iloc[0].split(" ")[0]

            def aggregator(x):
                if x.name == 'link_txt' or x.name == 'crawlid':
                    return "|||".join(x.tolist())
                # if x.name == 'mapped_score':
                #     return len(x.tolist())
                else:
                    return x.tolist()[0]


            gdf = pd.DataFrame(gr.agg(aggregator))
            gdf['dt'] = gdf.index
            gdf['date'] = map(lambda x: x.strftime('%Y-%m-%d'), gdf.dt)

            def splitter(txt, full_url, user, title, timestamp, referer):
                templ = """
        <div>
            <input class="toggle-box" id="header_%(sid)s" type="checkbox" >
            <label for="header_%(sid)s" onclick="log_expand_element('SmallCapNews', '%(sid)s');">%(title)s - (%(spam_id)s)</label>
            <div class="spam-content">
                <p> Author: %(user)s</p>
                <p> Timestamp: %(timestamp)s</p>
                <p> Title: %(title)s</p>
                <p> Url: <a target="_blank" href="http://%(full_url)s">%(full_url)s</a></p>
                <p> Referer: %(referer)s</p>
            </div>
        </div>
        """
                out = u""
                for _id in txt.split('|||'):
                    out += templ % {"spam_id": _id, 'sid': _id.replace('.', '_').replace('/', '_'),
                                    'full_url': full_url.replace("\n", "<br>"),
                                    "user": user, "referer": referer,
                                    "title": title, "timestamp": timestamp}

                return out

            gdf['content'] = map(splitter, gdf.crawlid, gdf.full_url, gdf.author,
                                 gdf.title, gdf.timestamp, gdf.referer)
            return gdf

        return df



    def add_glyph_to_plot(self, plot, hover_tool=False, evts_source=None):
        if evts_source is None:
            evts_source = self.evts_source

        glyph = CircleX(x='dt', y='mapped_score', fill_color='green',
                    line_color=None, size=13, fill_alpha=0.6)
        empty_glyph = CircleX(x='dt', y='mapped_score', fill_color='green',
                          line_color=None, size=13, fill_alpha=0.6)

        evts_renderer = plot.add_glyph(
            evts_source, empty_glyph,
            selection_glyph=glyph,
            nonselection_glyph=empty_glyph
        )
        # text_source = ColumnDataSource(data)
        # text = Text(
        #     x='dt', y='mapped_score', text='lbl', text_font_size='6pt',
        #     text_color='white', x_offset=-3, y_offset=5)
        # plot.add_glyph(self.evts_source, text)

        if hover_tool:
            hover = HoverTool(renderers=[evts_renderer])
            hover.tooltips =  """
            <div class="split-tooltip">
                <h3>Small Cap News</h3>
                <table><tbody>
                    <tr><td>Created on:</td><td> @timestamp</td></tr>
                    <tr><td>By:</td><td> @author</td></tr>
                    <tr><td>Title:</td><td> @title</td></tr>
                </table></tbody>
            </div>
            """
            hover.callback = Callback(code=HOVER_CB_TEMPL % "memex_forum_glyph")
            plot.add_tools(hover)

        self.evts_source.tags = ['small_cap_news']

        return evts_renderer

class SplitsFinder(EventsFinder):
    widget_name = 'splits_finder'
    name = 'splits'

    url = ES_ENDPOINT + "/edgar-base25/sub/_search?q=instance:%%22%(symbol)s%%22"
    glyph = Diamond(x='dt', y='mapped_score', fill_color='purple',
                    line_color=None, size=22, fill_alpha=0.6)
    empty_glyph = Diamond(x='dt', y='mapped_score', fill_color='purple',
                          line_color=None, size=22, fill_alpha=0.6)

    def cb_code(self, symbol):
        return ""
        url = "http://www.otcmarkets.com/stock/%s/news" % symbol
        url_yf_1 = "http://finance.yahoo.com/q/h?s=%s&t=" % symbol
        url_yf_2 = "T23:59:59-4:00"

        code = """

            if (window.last_sec_index == undefined){
                return false;
            }

            var dat = spam_source.get('data');
            var adsh = dat.adsh[window.last_sec_index];

            $.ajax(
            {
              dataType: 'json',
              url : '/edgar-base15/num/_search?q=adsh:' + adsh,
              method : 'GET',
              contentType : 'application/json'
            })
            .done(function( data ) {

                if (data != undefined && data.hits.hits.length > 0){
                    $("#info_dialog_content").html(
                      '<div> \
                        <h2>SEC EDGAR Details:</h2> \
                        <div style="margin-top: 10px;"> \
                            <ul> \
                            <li><div class="details-content"><strong>Tag:</strong> ' + data.hits.hits[0]._source['tag'] + '</div></li> \
                          </ul> \
                        </div> \
                      </div>'
                    );
                    $("#info_dialog").addClass('modalTarget');


                    //function reset_spams() {
                    //    spam_source.set('selected', window.new_selection_object);
                    //}
                    //setTimeout(reset_spams, 1000);
                }

              });


            msg = {
                activity: 'select',
                action: 'click',
                elementType: 'canvas',
                elementId: 'spam',
                elementGroup: 'chart_group',
                source: 'user',
                tags: ['query']
            };
            ale.log(msg);

        """ #% (url_yf_1, url_yf_2, url)
        return code


    def load_data(self, symbol, path='data/symbol_splits.csv', start_date=None):
        splits = pd.read_csv(path)
        splits['dt'] = pd.to_datetime(splits.date)

        if start_date:
            splits = tt[splits['dt'] >= start_date]

        splits = splits[splits['symbol'] == symbol]

        return splits

    def prepare_data(self, df, date_range):
        if len(df):
            df = pd.DataFrame(df)
            df['dt'] = pd.to_datetime(df['date'])
            df = df[(df['dt'] > date_range[0]) & (df['dt'] < date_range[1])]

            if not len(df):
                return {}

            data = self.app.source.data
            value = max(data['price']) - (max(data['price']) / 3.)
            # df['mapped_score'] = [value] * len(df['dt'])

            data = self.app.source.data
            # df['mapped_score'] = [max(data['price']) / 2.] * len(df['dt'])
            pmap = {d.date(): p for d, p in zip(data['dt'], data['price'])}
            mapped_score = []
            default = data['price'].mean()
            min_, max_ = min(data['price']), max(data['price'])
            for lrdt in df.dt:
                new = pmap.get(lrdt.date(), default)
                # print (lrdt, pmap[0])
                if new < default:
                    new += new * 0.05
                    new = min(new, max_)
                else:
                    new -= new * 0.05
                    new = max(new, min_)
                mapped_score.append(new)

            df['mapped_score'] = mapped_score

            df['lbl'] = ["S"] * len(df['dt'])
            df = df.sort('dt')

        return df

    def search(self, symbol, max_values):
        # SPAM
        self.evts = self.prepare_data(
            self.load_data(symbol),
            (min(self.app._df['dt']), max(self.app._df['dt']))
        )
        self.evts_source = ColumnDataSource(self.evts if len(self.evts) else {})

        names = dict(
            js_list_of_sources=str(list(self.layers.keys())).replace("'", ""),
            widget_name=self.widget_name, url=self.url,
            name=self.name, symbol=self.symbol,
        )

        code = self.evts_selection_cb_templ % names
        objs = {'evts_source': self.evts_source}
        callback = Callback(args=objs, code=code)
        self.evts_source.callback = callback

    def add_glyph_to_plot(self, plot, hover_tool=False, evts_source=None):
        if evts_source is None:
            evts_source = self.evts_source

        evts_renderer = plot.add_glyph(
            evts_source, self.empty_glyph,
            selection_glyph=self.glyph,
            nonselection_glyph=self.empty_glyph
        )
        # text_source = ColumnDataSource(data)
        text = Text(
            x='dt', y='mapped_score', text='lbl', text_font_size='6pt',
            text_color='white', x_offset=-3, y_offset=5)
        plot.add_glyph(evts_source, text)

        if hover_tool:
            hover = HoverTool(renderers=[evts_renderer])#, action=callback)
            # hover.mode='vline'
            hover.tooltips = OrderedDict([
                ("SPLIT on", "@date"),
                ("Company", "@company"),
                ("Announced", "@announced"),
                ("Payable", "@payable"),
                ("Optionable", "@optionable"),
                ("Ratio", "@ratio"),
            ])
            hover.tooltips =  """
            <div class="split-tooltip">
                <h3>Symbol Split</h3>
                <table><tbody>
                    <tr><td>SPLIT on:</td><td> @date</td></tr>
                    <tr><td>Company:</td><td> @company</td></tr>
                    <tr><td>Announced:</td><td> @announced</td></tr>
                    <tr><td>Payable:</td><td> @payable</td></tr>
                    <tr><td>Optionable:</td><td> @optionable</td></tr>
                    <tr><td>Ratio:</td><td> @ratio</td></tr>
                </table></tbody>
            </div>
            """
            hover.callback = Callback(code=HOVER_CB_TEMPL % "split_glyph")
            plot.add_tools(hover)

        return evts_renderer


class NewsFinder(EventsFinder):
    widget_name = 'news_slider'
    name = 'news'

    @classmethod
    def register_endpoint(cls, app):
        @app.route("/bokeh/%s/" % cls.name, methods=['GET', 'OPTIONS'])
        @crossdomain(origin="*", methods=['GET', 'POST'], headers=None)
        def serve_news():
            from utils import create_hist_data
            limit = int(request.args['limit'])
            serv = services[cls.name]
            return jsonify(values=create_hist_data(serv.evts, limit))

    def search(self, symbol, max_values):
        from utils import load_fake_spam, create_hist
        self.evts = spams = load_fake_spam(symbol, 20)
        slen = len(spams)
        source_data = dict()

        if slen:
            spams.index = spams.sdt
            source_data['sdt'] = list(spams.sdt)
            source_data['pd_ct'] = source_data['score'] = list(spams.score)
            source_data['s'] = list(spams.s)
            source_data['ssec'] = list(spams.ssec)
            self.evts_source = ColumnDataSource(spams if spams is not None else {})

            _max = max(self.app.source.data['price'])
            if _max > 1:
                mapped_score = spams.score * _max
            else:
                mapped_score = spams.score
            self.evts_source.add(list(mapped_score), 'mapped_score')

        self.evts_grpd = create_hist(spams)
        self.hist_source = ColumnDataSource(self.evts_grpd)


class IntervalFinder(object):
    name = ""
    widget_name = ""
    widget_title = ""
    callback_code = ""
    widget_defaults = dict(value=0, start=0, step=1)
    url = ""

    cb_code_templ = """
        // jsondata = JSON.stringify(jsondata);

        msg = {
            activity: 'select',
            action: 'click',
            elementType: 'dropdownlist',
            elementId: 'algorithm',
            elementSub: "%(name)s",
            elementGroup: 'input_group',
            source: 'user',
            tags: ['query']
        };
        ale.log(msg);

        url = "%(url)s?s=%(symbol)s&%(params)s;

        xhr = $.ajax({
            type: 'GET',
            url: url,
            contentType: "application/json",
            // data: jsondata,
            header: {
              client: "javascript"
            }
        });
        window.source = source;
        window.main_source = main_source;

        $("body").addClass("loading");
        // window.prev_loaded_flag = $('.bk-ui-slider')[0].id; // $('select[name=symbol_filter]')[0].id;
        dialog.set('visible', false);
        //check_loaded();

        xhr.done(function(data) {
            $("body").removeClass("loading");
            window.data = data;

            //source.get('data').top = data.values;
            //debugger;
            window.prev_loaded_flag = "done";
            if (data.results.length > 0){
                source_data = source.get('data');
                window.sd = source_data;
                source_data.bottom = [];
                source_data.values = [];
                source_data.start = [];
                source_data.end = [];
                for (i=0; i<data.results.length; i++){
                    var start =  data.results[i].start;
                    var end =  data.results[i].end;
                    source_data.bottom.push(0);
                    source_data.values.push(%(maxval)s);
                    source_data.start.push(start);
                    source_data.end.push(end);
                }
                source.trigger('change');
            }else{
                alert("No interval found with the selected method!");
            }
        })
        .fail(function (jqXHR, textStatus, errorThrown) {
            $("body").removeClass("loading");
            window.prev_loaded_flag = "done";
            alert("Error connecting to service: " + textStatus);
            dialog.set('visible', false);
         })
    """

    def __init__(self, symbol, app):
        self.periods = {}
        self.source = app.intervals_source
        self.obj = app
        self.symbol = symbol
        global services
        services[self.name] = self

    @classmethod
    def register_endpoint(cls):
        raise NotImplementedError()

    def create_objects(self):
        elems = [
            ('%s', self.widget), ('%s_source', self.source),
            ('%s_content', self.content), ('%s_confirm_button', self.confirm_button),
             # ('%s_min_duration', self.min_duration),
            ('%s_min_quiet_days', self.min_quiet_days),
            ('%s_quiet_tol', self.quiet_tol),
            ('%s_min_growth_days', self.min_growth_days),
            ('%s_max_growth_days', self.max_growth_days),
            ('%s_growth_tol', self.growth_tol),
        ]
        d = {templ % self.name: el for templ, el in elems}
        return d

    def search(self):
        raise NotImplementedError()

    @property
    def widget(self):

        self.descr_box = Paragraph(text=self.description)

        self.min_quiet_days = TextInput(title="Minimum quiet days",
                                        name='min_quiet_days', value="10")
        self.quiet_tol = TextInput(title="Quiet tolerance",
                                        name='quiet_tol', value="0.05")
        self.min_growth_days = TextInput(title="Minimum growth days",
                                        name='min_growth_days', value="1")
        self.max_growth_days = TextInput(title="Maximum growth days",
                                        name='max_growth_days', value="30")
        self.growth_tol = TextInput(title="growth_tol",
                                        name='Growth tolerance', value="0.5")
        # self.min_duration = min_duration = TextInput(
        #     title="Min Duration (ticks in a row)", name='min_duration', value="10"
        # )

        self.content = main_tab = vplot(self.descr_box,
                                        self.min_quiet_days,
                                        self.quiet_tol,
                                        self.min_growth_days,
                                        self.max_growth_days,
                                        self.growth_tol) #, min_duration)
        self.confirm_button = confirm_button = Button(
            label="Confirm", type="success", name='confirm_add_chart')
        dialog = Dialog(buttons=[confirm_button], content=main_tab, visible=False)

        names = dict(
            url=self.url,
            params=('min_quiet_days=" + min_quiet_days.get("value")'
                    '+ "&quiet_tol=" + quiet_tol.get("value")'
                    '+ "&min_growth_days=" + min_growth_days.get("value")'
                    '+ "&max_growth_days=" + max_growth_days.get("value")'
                    '+ "&growth_tol=" + growth_tol.get("value")'),
                   # 'min_quiet_days=" + max_intervals.get("value")',
                    # 'min_quiet_days=" + max_intervals.get("value")',
                   #+"&p=" + min_duration.get('value')""",
            maxval=max(self.obj.source.data['price']),
            symbol=self.symbol,
            name=self.name
        )

        objs = dict(
            min_quiet_days=self.min_quiet_days, quiet_tol=self.quiet_tol,
            min_growth_days=self.min_growth_days, max_growth_days=self.max_growth_days,
            growth_tol=self.growth_tol,
            # min_duration=min_duration,
            dialog=dialog,
            source=self.obj.intervals_source, main_source=self.obj.source)


        code = self.cb_code_templ % names

        callback = Callback(args=objs, code=code)
        self.confirm_button.callback = callback
        dialog.buttons = [confirm_button]
        return dialog


class PeaksFinder(IntervalFinder):
    url = '/bokeh/peaks/'
    name = 'PEAKS'
    label = 'peaks'
    description = "Search for the intervals where the mean price did not " \
                  "deviate by more than a given percentage, for a given number" \
                  " of days, and then has an overall growth of more than a " \
                  "given percentage for a given number of days."
class Steinberg(IntervalFinder):
    url = 'http://10.1.93.203:8866/query'
    name = 'TICKS_IN_ROW'
    label = 'ticks in a row'
    description = "Find N ticks in a row"

    @property
    def widget(self):

        self.descr_box = Paragraph(text=self.description)

        self.limit = TextInput(title="Limit", name='limit', value="10")

        self.content = main_tab = vplot(self.descr_box,
                                        self.limit) #, min_duration)
        self.confirm_button = confirm_button = Button(
            label="Confirm", type="success", name='confirm_add_chart')
        dialog = Dialog(buttons=[confirm_button], content=main_tab, visible=False)

        names = dict(
            url=self.url,
            params=('limit=" + limit.get("value")'),
            maxval=max(self.obj.source.data['price']),
            symbol=self.symbol,
            name=self.name
        )

        objs = dict(
            limit=self.limit,
            dialog=dialog,
            source=self.obj.intervals_source, main_source=self.obj.source)


        code = self.cb_code_templ % names

        callback = Callback(args=objs, code=code)
        self.confirm_button.callback = callback
        dialog.buttons = [confirm_button]
        return dialog

    def create_objects(self):
        elems = [
            ('%s', self.widget), ('%s_source', self.source),
            ('%s_content', self.content), ('%s_confirm_button', self.confirm_button),
            # ('%s_min_duration', self.min_duration),
            ('%s_limit', self.limit),
        ]
        d = {templ % self.name: el for templ, el in elems}
        return d


available = [
    SpamFinder,
    SECFillingsFinder,
    SplitsFinder,
    SmallCapNews,
    # ForumDataFinder,
    MemexForumDataFinder,
    # NewsFinder
]
services = {}

interval_finders = [PeaksFinder]
interval_services = {}
