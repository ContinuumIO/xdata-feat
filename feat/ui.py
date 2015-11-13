import pandas as pd
from bokeh import plotting

from collections import OrderedDict
import numpy as np
from bokeh.models import (HoverTool, BoxSelectTool, BoxZoomTool, TapTool,
                          WheelZoomTool, PanTool,
                          Circle, ColumnDataSource, Range1d, LinearAxis,
                          DatetimeTickFormatter, DatetimeAxis, Text)
from bokeh.models.glyphs import Quad
import callbacks
import utils
import factories
from bokeh.models.actions import Callback, OpenURL
from bokeh.models.widgets import VBoxForm

PLOTS_WIDTH = 850
def get_xformatter():
    return DatetimeTickFormatter(
        formats=dict(
            months=["%b '%y"],
            days=["%d %b '%y"]
        )
    )


def style_axis(plot):
    plot.axis.minor_tick_in=None
    plot.axis.minor_tick_out=None
    plot.axis.major_tick_in=None
    plot.axis.major_label_text_font_size="10pt"
    plot.axis.major_label_text_font_style="normal"
    plot.axis.axis_label_text_font_size="10pt"

    plot.axis.axis_line_color='#AAAAAA'
    plot.axis.major_tick_line_color='#AAAAAA'
    plot.axis.major_label_text_color='#666666'

    plot.axis.major_tick_line_cap="round"
    plot.axis.axis_line_cap="round"
    plot.axis.axis_line_width=1
    plot.axis.major_tick_line_width=1


def create_sparkline(obj):
    sparkline_toolset = "box_select"

    # Generate a figure container
    plot = plotting.figure(
        height=150, width=PLOTS_WIDTH, tools=sparkline_toolset,
        x_axis_location="above", y_axis_label='Adj. Close Price',
        # title=obj.selected_symbol,
        x_axis_type="datetime", toolbar_location=None,
        outline_line_color=None,
        name="small_plot"
    )
    plot.min_border_bottom = plot.min_border_top = 0
    plot.background_fill = '#EEEEEE'
    plot.border_fill = "white"

    # Create source and glyphs for the P&D orange boxes
    psource = ColumnDataSource(obj.intervals_source.data)

    glyph = Quad(top='values', bottom='bottom', left='start', right='end',
                 fill_color='orange', fill_alpha=0.3, line_alpha=0)
    empty_glyph = Quad(top='values', bottom='bottom', left='start', right='end',
                 fill_color='orange', fill_alpha=0.3, line_alpha=0)
    plot.add_glyph(
            psource, glyph,
            selection_glyph=glyph,
            nonselection_glyph=empty_glyph
        )
    # psource.tags = ['pump_and_dumps']

    # Create source and glyphs for the light blue boxes showed
    # when an interval is selected
    selection_source = ColumnDataSource()
    for k in ['end', 'values', 'start', 'bottom']:
        selection_source.add([], k)
    plot.quad(top='values', bottom='bottom', left='start', right='end',
              source=selection_source, color='#c6dbef', fill_alpha=0.5)

    for k in ['scatter', 'line']:
        plot = factories.makers[k](
            'dt', ['price'], source=obj.source, colors=['#666666'],
            p=plot
        )
    obj.source.tags = ['min_source']

    # Customize select tool
    select_tool = plot.select(dict(type=BoxSelectTool))
    select_tool.dimensions = ['width']
    zoom_tool = plot.select(dict(type=BoxZoomTool))
    zoom_tool.dimensions = ['width']

    maxval = max(obj.source.data['price'])

    objs = {
        # TODO: PASSING A PLOT OR ITS RANGE TO A CB MAKES IT BREAK EVT TAPTOOL!!!!!
        'spark_source': obj.source,
        'selection_source': selection_source,
        'evts_source': obj._plugins[0].evts_source,
        'spam_source': obj.spam_source,
        'sec_source': obj.sec_source,

    }
    callback = Callback(args=objs, code=callbacks.small_selection_plot % maxval)
    obj.source.callback = callback

    plot.ygrid.grid_line_color = None

    style_axis(plot)
    plot.tags = ['small_plot']
    add_evt_plugins(obj, plot, copy_source=True)
    return plot


def create_main_plot(obj, **kwargs):
    TOOLS="crosshair,pan,box_zoom,wheel_zoom,reset,hover"#,tap"

    # Generate a figure container
    plot = plotting.figure(
        height=350, width=PLOTS_WIDTH, tools=TOOLS, title="",#obj.selected_symbol,
        toolbar_location="right", y_axis_label='Closing price, US dollars',
        y_range = [min(obj.main_source.data['price']) * 0.8,
                   max(obj.main_source.data['price']) * 1.1],
        x_axis_type="datetime",
        outline_line_color=None,
        name="main_plot",
        **kwargs
    )
    plot.min_border_bottom = plot.min_border_top = 5
    # plot.background_fill = '#868687'
    plot.background_fill = 'white'
    plot.border_fill = "white"
    plot.grid.grid_line_color = "whitesmoke"
    plot.grid.grid_line_dash = 'solid'
    plot.grid.grid_line_width = 1

    data = obj.intervals_source.data

    # plot.quad(top='values', bottom='bottom', left='start', right='end',
    #           source=obj.intervals_source, color='#FFFFCC', fill_alpha=0.3)
    glyph = Quad(top='values', bottom='bottom', left='start', right='end',
                 fill_color='#FFFFCC', fill_alpha=0.5, line_alpha=0)
    empty_glyph = Quad(top='values', bottom='bottom', left='start', right='end',
                 fill_color='#FFFFCC', fill_alpha=0.5, line_alpha=0)
    plot.add_glyph(
            obj.intervals_source, glyph,
            selection_glyph=glyph,
            nonselection_glyph=empty_glyph
        )
    obj.intervals_source.tags = ['pump_and_dumps']

    volume_source = ColumnDataSource(obj.main_source.data)
    plot.extra_y_ranges = {"vol": Range1d(
        start=min(volume_source.data['Volume']),
        end=max(volume_source.data['Volume']))
    }
    volume_source.tags = ['volume']

    # add_trends_layer(obj, plot)


    # COMMENTED CODE TO CREATE TEXT LABELS
    # xs = np.empty(2*len(data['start'])-1, dtype=np.int)
    # xs[::2] = data['start'][:]
    # xs[1::2] = data['start'][1:]
    # ldata = {'x': [], 'y': []}
    # dts = map(lambda x: utils.to_seconds(x) * 1000, obj.main_source.data['dt'])
    # for x in data['start']:
    #     ind = 0
    #     for ind, dt_ in enumerate(dts):
    #         if dt_ > x:
    #             break
    #
    #     ldata = {'x': [], 'y': []}
    #     ldata['x'].append(x)
    #     ldata['x'].append(x)
    #     ldata['y'].append(obj.main_source.data['price'][ind])
    #     ldata['y'].append(max(obj.main_source.data['price']) / 2.)
    #
    #     text_lines = ColumnDataSource(ldata)
    #     plot.line(
    #         'x', 'y', line_color='#ff0000',
    #         line_alpha=0.5, line_width=1, source=text_lines
    #     )


    # data = {'start': data['start'], 'end': data['end'], 'lbl_start': ['Start P&D'] * len(data['start']),
    #         'y': [max(obj.main_source.data['price']) / 2.] * len(data['start'])}
    #
    # text_source = ColumnDataSource(data)
    # text = Text(x='start', y='y', text='lbl_start', text_font_size='8pt', text_color='#EEEEEE', angle=45)
    # plot.add_glyph(text_source, text)

    # plot.line('dt', 'vol_delta', line_color='black',
    #           line_alpha=0.5, line_width=1, source=obj.source)

    # plot.quad(top='values', bottom='bottom', left='start', right='end',
    #           source=psource, color='orange', fill_alpha=0.3)



    # plot.line('dt', 'price',
    #       line_color='red',
    #       line_width=1,
    #       source=obj.djia_source,
    #       y_range_name="djia")


    plot.line('dt', 'Volume',
              # line_color='#AAAAAA',
              line_color='#EEEEEE',
              line_width=1,
              source=volume_source,
              y_range_name="vol")


    plot.line('dt', 'price',
              line_color='black',
              line_width=1,
              source=obj.main_source)
    obj.main_source.tags = ['main_source']

    # TODO: Why this is not working?
    # plot.add_layout(LinearAxis(y_range_name="vol"), 'right')

    line_renderers = [plot.renderers[-1]]

    hover =plot.select(dict(type=HoverTool))
    hover.mode='vline'
    hover.tooltips = OrderedDict([
        ("Volume", "@Volume"),
        ("Low", "$ @Low"),
        ("High", "$ @High"),
        ("Open", "$ @Open"),
        ("Close", "$ @Close"),
        ("Adj. Close", "$ @price_fmt"),
        ("Exch. Timestamp", "@exch_ts"),
        # ("Session Date", "@exch_date")

    ])
    hover.renderers = line_renderers
    hover.callback = Callback(code=callbacks.line_hover)
    zoom_tool = plot.select(dict(type=BoxZoomTool))
    zoom_tool.dimensions = ['width']

    plot.select(dict(type=PanTool)).dimensions = ['width']
    plot.select(dict(type=WheelZoomTool)).dimensions = ['width']



    xaxis = plot.select(dict(type=DatetimeAxis))
    xaxis.formatter=get_xformatter()

    style_axis(plot)
    plot.tags = ['main_plot']
    add_evt_plugins(obj, plot)#, hover_tool=True)

    return plot


def add_evt_plugins(obj, plot, hover_tool = False, copy_source=False):
    colors = ["red", "blue", "orange", "green"][:len(obj._plugins)]
    code = ""
    objs = {'plot': plot}
    for pl in obj._plugins:
        if copy_source:
            evts_source = ColumnDataSource(pl.evts_source.data)
        else:
            evts_source = pl.evts_source

        renderer = pl.add_glyph_to_plot(plot, hover_tool=hover_tool, evts_source=evts_source)
        # tap =plot.select(dict(type=TapTool))
        _code = pl.cb_code(obj.selected_symbol)
        if _code:
            code=_code
        objs['%s_source' % pl.name] = pl.evts_source

        if not getattr(obj,'%s_source' % pl.name):
            setattr(obj, '%s_source' % pl.name, pl.evts_source)

    callback = Callback(args=objs, code=code)

    tap = TapTool(
        # renderers=[renderer],
        action=callback)
    plot.add_tools(tap)
    tap.action = callback

    return plot


def add_trends_layer(obj, plot):
    if obj.selected_symbol in obj.trends_source.data:
        plot.extra_y_ranges["trends"] = Range1d(
            start=min(obj.trends_source.data[obj.selected_symbol]),
            end=max(obj.trends_source.data[obj.selected_symbol]))

        plot.line(
            'dt', obj.selected_symbol,
            line_color='blue', line_alpha=0.3,
            line_width=2,
            source=obj.trends_source,
            y_range_name="trends"
        )


def create_trends_plot(obj):
    plot = plotting.figure(
        height=50, width=PLOTS_WIDTH, tools='',
        x_range = obj.main_plot.x_range,
        x_axis_type="datetime", toolbar_location=None,
    )
    plot.line(
            'dt', obj.selected_symbol,
            line_color='blue',
            line_width=1,
            source=obj.trends_source,
            y_range_name="trends"
        )

    plot.yaxis.axis_label = "Vol. Var."
    style_tiny_plots(plot)
    return plot


def style_tiny_plots(plot):
    plot.min_border_bottom = plot.min_border_top = 0
    plot.background_fill = 'whitesmoke'
    plot.border_fill = "white"

    plot.xaxis.visible = False

    plot.yaxis.axis_label_text_font_size = '6pt'
    # clean the figure from grid, axis, etc..
    plot.axis.axis_line_color = None
    # plot.xgrid.grid_line_color = None
    # plot.ygrid.grid_line_color = None
    plot.yaxis.major_label_text_font_size = '6pt'
    #plot.axis.major_tick_line_color = None

    plot.yaxis.minor_tick_line_color = None
    plot.ygrid[0].ticker.desired_num_ticks = 4
    plot.grid.grid_line_color = "white"
    plot.grid.grid_line_width = 2

    xaxis = plot.select(dict(type=DatetimeAxis))
    xaxis.formatter=get_xformatter()

def create_layout(obj):
    # Get the widget for all available plugins and add them

    interval_plugins = {pl.name: getattr(obj, pl.name)
                        for pl in obj._interval_plugins}
    names = dict(
        js_list_of_sources=str({k: k for k in interval_plugins.keys()}).replace("'", "")
    )
    code = callbacks.window_selector % names
    objs = dict(interval_plugins)
    callback = Callback(args=objs, code=code)
    obj.window_selector.callback = callback
    callback.args['interval_selector'] = obj.window_selector


    # configure button to open pump and dump detection (Poulson Algorithm)
    code = callbacks.btn_detect_pumps % names
    callback = Callback(args=objs, code=code)
    obj.btn_detect_pumps.callback = callback

    # add all elements of the main dashboard
    main_view = plotting.hplot(
        plotting.vplot(
            obj.ts_filters_plot, obj.main_plot,
        ),
    )

    # add spams table to spams tab
    obj.spam_tab.child = plotting.hplot(obj.spam_table)

    # create
    obj.vpeaks = plotting.vplot(obj.PEAKS)
    # vsteinberg = plotting.vplot(obj.TICKS_IN_ROW)
    obj.children = [plotting.vplot(
        # obj.symbol,
        # obj.tabs,
        main_view,
        # vpeaks, # add peaks plugin dialog view
        # vsteinberg,
        # obj.dialog_loading,
    )]

def create_simple_layout(obj):
    # TODO: Seems that DateRangeSlider is broken on latest release. It'd be
    #       nice to add it when issue is fixed
    # start = datetime.date(2010, 1, 1)#'2010-01-01'
    # end = datetime.date(2015, 1, 1)#'2015-01-01'
    # obj.dr = DateRangeSlider(
    #     title="Period:", name="period", value=(start, end),
    #     bounds=(start, end), range=(dict(days=1), None)
    # )
    # Get the widget for all available plugins and add them

    interval_plugins = {pl.name: getattr(obj, pl.name)
                        for pl in obj._interval_plugins}
    names = dict(
        js_list_of_sources=str({k: k for k in interval_plugins.keys()}).replace("'", "")
    )
    code = callbacks.window_selector % names
    objs = dict(interval_plugins)
    callback = Callback(args=objs, code=code)
    obj.window_selector.callback = callback
    callback.args['interval_selector'] = obj.window_selector

    # configure button to open pump and dump detection (Poulson Algorithm)
    code = callbacks.btn_detect_pumps % names
    callback = Callback(args=objs, code=code)
    obj.btn_detect_pumps.callback = callback

    main_view = plotting.hplot(
        plotting.vplot(
            obj.ts_filters_plot,
            obj.main_plot,
            # obj.cp_plot,
            # obj.trends_plot
        ),
    )

    # add spams table to spams tab
    obj.spam_tab.child = plotting.hplot(obj.spam_table)

    # create
    obj.vpeaks = plotting.vplot(obj.PEAKS)
    obj.children = [plotting.vplot(
        main_view,
    )]

