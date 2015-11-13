from __future__ import print_function

import time

from bokeh.server.utils.plugins import object_page
from bokeh.server.app import bokeh_app

from bokeh.plotting import curdoc, ColumnDataSource, Plot
from bokeh.models.widgets import (Paragraph, Button, Select, DataTable,
                                  TableColumn, StringFormatter, NumberFormatter,
                                  StringEditor, IntEditor, NumberEditor,
                                  Panel, Tabs, Slider, VBoxForm, Dialog)

from bokeh.io import VBox, vplot
from bokeh.models.actions import Callback

from bokeh.models import (Instance, List, String)

import plugins
import pumps 
import utils, ui, callbacks
import config
import pandas as pd

# TODO: This folder should be taken from config!!!!
SECURITIES_FOLDER = 'data/securities/'

TOOLS="resize,crosshair,pan,wheel_zoom,box_zoom,reset,tap,previewsave,box_select,poly_select,hover,lasso_select"
active_charts = {}
saved_annotations = {}
current_selection = None
symbols_filtered = {}

pre_filtered_data = {}

class TableBoard(VBox):
    extra_generated_classes = [["TableBoard", "TableBoard", "VBox"]]
    jsmodel = "TableBoard"

    securities = List(String)
    main_tab = Instance(Panel)
    table_stocks_rank = Instance(DataTable)
    source_stocks_rank = Instance(ColumnDataSource)

    @classmethod
    def create_objects(cls, securities):

        ranks = utils.get_pumps_rank()
        quotient_metrics = utils.get_quotient_metrics()
        ranks['quotient'] = quotient_metrics['quotient']

        foo = lambda x: utils.spam_counts.get(x, 0)
        ranks['spams'] = map(foo, ranks['symbol'])
        ranks = ranks.sort('quotient', ascending=False)

        cls._pre_filtered_ranks = {
            'All': {k: ranks[k] for k in ranks.columns},
            'Stocks with Spam': dict(ranks[ranks['symbol'].
                                     isin(plugins.spam_counts.keys())].
                                     sort('quotient', ascending=False)),
            'Stocks without Spam': dict(ranks[~ranks['symbol'].
                                        isin(plugins.spam_counts.keys())].
                                        sort('quotient', ascending=False)),
        }

        source_stocks_rank = ColumnDataSource(cls._pre_filtered_ranks['Stocks with Spam'])
        table_stocks_rank = DataTable(
            source=source_stocks_rank, width=785, height=400,
            selectable=True, editable=True,
            columns=[
                TableColumn(field='symbol', title='symbol', editor=StringEditor()),
                TableColumn(field='quotient', title='quotient', editor=StringEditor()),
                TableColumn(field='rank', title='rank', editor=StringEditor()),
                TableColumn(field='spams', title='spams', editor=StringEditor()),
            ])

        callback = Callback(
            args={'tr': table_stocks_rank, 'sr': source_stocks_rank},
            code=callbacks.source_stocks_rank
        )
        source_stocks_rank.callback = callback
        return locals()

    @classmethod
    def create(cls, symbol):
        """One-time creation of app's objects.

        This function is called once, and is responsible for
        creating all objects (plots, datasources, etc)
        """
        securities = utils.seek_securities(SECURITIES_FOLDER)
        obj = cls(securities=securities)
        obj = TableBoard.recreate_all(obj)
        return obj

    @staticmethod
    def recreate_all(obj):
        # get SYMBOL data
        for name, attr in obj.create_objects(obj.securities).items():
            if name != 'cls':
                try:
                    setattr(obj, name, attr)
                except AttributeError:
                    pass

        obj.children = [
            obj.table_stocks_rank,
        ]

        return obj

    def exec_filter_symbol(self, obj,attrname, old, new):
        TableBoard.recreate_all(self)

        dat = TableBoard._pre_filtered_ranks[new]
        self.source_stocks_rank.data = dat
        self.symbol_filter.value = new
        curdoc().add(self)

class StaticDash(object):
    @classmethod
    def create_objects(cls, symbol, df, securities):
        descr_box = Paragraph(text='content loading...')

        btn_close_loading = Button(label='Close Loading')
        dialog_loading = Dialog(
            title='loading', content=vplot(descr_box), name='loading_dialog',
            buttons=[btn_close_loading], visible=False)

        source_data = dict(df)
        main_source = ColumnDataSource(dict(df))
        source = ColumnDataSource(source_data)

        # TODO: REMOVE THIS COMMENTED CODE! IT'S JUST THE PREVIOUS
        # VERSION USED BEFORE NEW P&D Cached results and algorithm
        # get the cached results of the P&D algorithm computed with the
        # "default" configuration
        # intervals = utils.cached_pumps.get(symbol, pumps.to_dicts(((),(),(),(),(),())))
        # intervals['bottom'] = [0] * len(intervals['start'])
        # intervals['values'] = [max(df['price'])] * len(intervals['start'])
        #
        # intervals = pd.DataFrame(intervals)

        # new version
        stats = utils.get_symbols_cached_stats()[symbol]
        intervals = pd.DataFrame(stats)
        intervals['bottom'] = [0] * len(intervals['start'])
        intervals['values'] = [max(df['price'])] * len(intervals['start'])

        conv = lambda x: utils.to_seconds(pd.to_datetime(x))

        intervals = intervals[
            (pd.to_datetime(intervals['start']) > conv(config.date_range[0])) &
            (pd.to_datetime(intervals['start']) < conv(config.date_range[1]))
        ]

        # Create P&Ds intervals DataSource
        intervals_source = ColumnDataSource(intervals)
        source.tags = ['main_source']

        trends = utils.load_trends_data(symbol, start_date=min(df['dt']))
        trends_source = ColumnDataSource(trends)

        trades = Slider(
            title="trades", name='trades',
            value=0, start=0, end=124, step=1
        )

        # Selectors
        symbol = Select.create(
            options=securities, value=symbol, name='symbol', title=""
        )
        window_selector = Select.create(
            options=['---'], name='period_selector', title="Search intervals with:"
        )
        symbol_filter = Select.create(
            options=['All', 'Stocks with Spam', 'Stocks without Spam'],
            name='symbol_filter', title="Filter Symbols:",
            value='Stocks with Spam'
        )
        callback = Callback(
            args={'symbol_filter': symbol_filter,
                  'dialog_loading': dialog_loading},
            code=callbacks.symbol_filter
        )
        symbol_filter.callback = callback


        btn_detect_pumps = Button(label='Configure P&D Detection', name='config_pumps')

        main_tab = Panel(title="Main")
        tabs = Tabs()

        # Create STOCKS TABLE
        ranks = utils.get_pumps_rank()
        # quotient_metrics = utils.get_quotient_metrics()
        # ranks['quotient'] = quotient_metrics['quotient']

        foo = lambda x: utils.spams_count.get(x, 0)
        ranks['spams'] = map(foo, ranks['symbol'])
        ranks = ranks.sort(['spams', 'vol_quotient'], ascending=False)

        cls._pre_filtered_ranks = {
            'All': {k: ranks[k] for k in ranks.columns},
            'Stocks with Spam': dict(ranks[ranks['spams'] > 0].
                                     sort('vol_quotient', ascending=False)),
            'Stocks without Spam': dict(ranks[ranks['spams'] == 0].
                                        sort('vol_quotient', ascending=False)),
        }

        source_stocks_rank = ColumnDataSource(cls._pre_filtered_ranks['All'])


        table_stocks_rank = DataTable(
            source=source_stocks_rank, width=560, height=450,
            selectable=True, editable=True,
            columns=[
                TableColumn(field='symbol', title='symbol', width=130, editor=StringEditor()),
                TableColumn(field='vol_quotient', title='volume ratio', editor=StringEditor(),
                            default_sort='descending'),
                TableColumn(field='risk_score', title='risk', width=100, editor=StringEditor(),
                            default_sort='descending'),
                TableColumn(field='spams', title='spams', width=130, editor=StringEditor(),
                            default_sort='descending'),
            ])

        callback = Callback(args={'tr': table_stocks_rank, 'sr': source_stocks_rank, 'symb': symbol,
                                  'dialog_loading': dialog_loading},
                            code=callbacks.source_stocks_rank)
        source_stocks_rank.callback = callback

        return locals()

    @classmethod
    def create(cls, symbol):
        """One-time creation of app's objects.

        This function is called once, and is responsible for
        creating all objects (plots, datasources, etc)
        """
        securities = utils.seek_securities(SECURITIES_FOLDER)
        obj = cls()
        obj.securities=securities
        obj.selected_symbol=symbol
        obj = cls.recreate_all(obj)
        
        return obj

    @staticmethod
    def recreate_all(obj):
        # get SYMBOL data
        obj._df = _df = utils.load_symbol_low_res(
            obj.selected_symbol, SECURITIES_FOLDER
        )
        # get DOW JONES data and filter to have only data matching the symbol interval
        # obj._dfdjia = djia = utils.load_symbol_low_res("DJIA", SECURITIES_FOLDER)
        # obj._dfdjia = djia[djia['dt'] >= min(_df['dt'])]
        # obj.djia_source = ColumnDataSource(dict(obj._dfdjia))

        # create application objects
        obj._plugins = []
        obj._interval_plugins = []
        for name, attr in obj.create_objects(obj.selected_symbol, _df, obj.securities).items():
            if name != 'cls':
                try:
                    setattr(obj, name, attr)
                except AttributeError:
                    print ("skipping attribute not declared: ", name)

        for plg_cls in plugins.available:
            # TODO: We probably don't need this max value! It should be only for the histograms
            # on the main plot
            plugin = plg_cls(obj.selected_symbol, 10, obj)
            obj._plugins.append(plugin)
            for name, attr in plugin.create_objects().items():
                try:
                    setattr(obj, name, attr)
                except:
                    print ("ERRROR registering", name, "from plugin", plugin.widget_name)
                    pass

        for plg_cls in plugins.interval_finders:
            plugin = plg_cls(obj.selected_symbol, obj)
            obj._interval_plugins.append(plugin)
            obj.window_selector.options.append(plugin.name)
            for name, attr in plugin.create_objects().items():
                try:
                    setattr(obj, name, attr)
                except:
                    print ("ERRROR registering", name, "from interval plugin", plugin.widget_name)
                    pass

        obj.main_plot = ui.create_main_plot(obj)
        sp = obj.ts_filters_plot = ui.create_sparkline(obj)
        ui.create_simple_layout(obj)

        return obj

    def change_symbol(self, obj,attrname, old, new):
        self.selected_symbol = new
        Dashboard.recreate_all(self)

        if symbols_filtered:
            self.source_stocks_rank.data = symbols_filtered
        curdoc().add(self)


    def exec_filter_symbol(self, obj,attrname, old, new):
        Dashboard.recreate_all(self)

        dat = Dashboard._pre_filtered_ranks[new]
        self.source_stocks_rank.data = dat
        self.symbol_filter.value = new
        curdoc().add(self)

