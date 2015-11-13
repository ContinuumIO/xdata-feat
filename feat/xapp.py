import pandas as pd
from collections import OrderedDict
from bokeh.plot_object import PlotObject
from bokeh.server.utils.plugins import object_page
from bokeh.server.app import bokeh_app
from bokeh.plotting import curdoc, cursession, ColumnDataSource
from bokeh.crossfilter.models import CrossFilter
from bokeh.sampledata.autompg import autompg
from bokeh.models.widgets import VBox, HBox, Paragraph, Button, TableColumn, DataTable, DateEditor, DateFormatter, IntEditor,\
    Select, DataTable, TableColumn, StringFormatter, NumberFormatter, StringEditor, IntEditor, NumberEditor, \
    SelectEditor, MultiSelect, Panel, Tabs

from bokeh.models.widgets import (HBox, VBox, VBoxForm, PreText, Dialog, TextInput, AutocompleteInput,
                                  Select, AppHBox, AppVBox, AppVBoxForm, CheckboxGroup)

from bokeh.sampledata.iris import flowers
from bokeh import charts, plotting

from bokeh.palettes import brewer

from bokeh.models import ServerDataSource, BlazeDataSource
from bokeh.transforms import line_downsample
from bokeh.models import HoverTool
from bokeh.simpleapp import simpleapp

from StringIO import StringIO
import cols_schema
import os

import factories, actions

FLASHCRASH_FOLDER = '/Users/fpliger/dev/projects/xdata/xdata-2015/bokeh_app/xapp/data/flash_crash/'
SECURITIES_FOLDER = '/Users/fpliger/dev/projects/xdata/xdata-2015/bokeh_app/xapp/data/flash_crash_securities_csvs/'
# FLASHCRASH_FOLDER = '/team6/flash_crash/'
# SECURITIES_FOLDER = '/team6/flash_crash_securities_csvs/'

TOOLS="resize,crosshair,pan,wheel_zoom,box_zoom,reset,tap,previewsave,box_select,poly_select,hover,lasso_select"
active_charts = {}
saved_annotations = {}
current_selection = None

def seek_securities():
    secs = set()
    for _file in os.listdir(SECURITIES_FOLDER):
        if not _file.startswith("0") and \
            not _file.startswith(".") and \
                os.stat(os.path.join(SECURITIES_FOLDER, _file)).st_size == 0:
            secname = "_".join(_file.replace('.txt', '').split("_")[:-1])
            if load_symbol(secname) is not None:
                secs.add(secname)
    return sorted(list(secs))

def load_crashes():
    raw_cols = [
        'sec', 'end_date', 'change', 'as_percent', 'upticks', 'downticks',
        'price', 'tickwindow', 'as_percent_per_sec', 'change_per_sec', 'start_date', 'extra'
        ]
    path = os.path.join(FLASHCRASH_FOLDER, 'nxcore_diff_selects_fc_10sec.txt')
    crash_df = pd.read_csv(path, sep='\t', names=raw_cols, parse_dates=['end_date', 'start_date'])
    grsec = crash_df.groupby('sec')
    counted = grsec.count()
    summed = grsec.sum()
    summed['crashes'] = counted['change']
    summed['sec'] = summed.index
    return summed

def load_symbol(symbol):
    base_path = SECURITIES_FOLDER + '%s_0%i.txt'
    merged = None
    for i in range(2, 7):
        # TODO: Check is we can avoid this and just have standard csv format...
        path = base_path % (symbol, i)
        cols = [x[0] for x in cols_schema.schema]
        raw_cols = ['sec', 'date', 'rec']
        try:
            rdf = pd.read_csv(path, sep='\t', names=raw_cols)
            sdf = pd.read_csv(
                StringIO('\n'.join(rdf['rec'])), sep=',', names=cols,
                parse_dates={'dt': [u'System Date', u'System Time']}
            )
            try:
                sdf = sdf.sort('dt')
                if merged is None:
                    merged = sdf
                else:
                    merged = merged.append(sdf)
            except KeyError:
                pass
        except TypeError:
            pass

    return merged


SECURITIES = seek_securities()

SYMBOL = 'pLO.U14.10950C'
df = load_symbol(SYMBOL)
index = df.pop('dt')

num_columns = [col for col, type_ in cols_schema.numeric_columns]
df = df[num_columns]

for name in num_columns:
    stdv = df[name].std()
    values = [stdv for x in df.index]
    df['%s_std_dv' % name] = values

df['ind'] = list(range(len(index)))

cdf = load_crashes()
cdf['ind'] = range(len(cdf.index))
chart_types = sorted(factories.configs.keys())

def create_crashes_scatter():
    from bokeh.plotting import figure
    p = figure(tools="crosshair,pan,box_select,wheel_zoom,box_zoom,reset,hover,previewsave", height=300,
               x_axis_label='change', y_axis_label='# crashes')
    p.circle('change', 'crashes', color='#A6CEE3',
           source=csource, legend='Crashes X Change', x_axis_label='change', y_axis_legend='# crashes'
           )

    hover =p.select(dict(type=HoverTool))
    hover.tooltips = OrderedDict([
        ("index", "$index"),
        ("change", "@change"),
        ("crashes", "@crashes"),
        ("symbol", "@sec"),
    ])
    return p

@simpleapp()
def dashboard():
    """
    Creates the main app objects
    """
    # TODO: Should find a better design and remove those global objs...
    global source
    global csource

    source = ColumnDataSource(df)
    source.tags = ['main_source']

    csource = ColumnDataSource(cdf)
    csource.tags = ['crash_source']

    select_sec = Select.create(options=SECURITIES, name='select_sec', title="")

    asel = Select.create(options=df.columns, name='field_to_add', title="")
    chart_sel = Select.create(options=chart_types, name='chart_to_add', title="")

    msel = MultiSelect.create(options=[], name='ms')
    abutton = Button(label="add", type="success", name='add_button')
    rbutton = Button(label="remove", type="danger", name='remove_button')
    add_chart_button = Button(label="add chart", type="success", name='add_chart')


    data_table = DataTable(source=source, editable=True, width=500, height=400)
    ccolumns = [TableColumn(field=x, title=x, editor=NumberEditor()) for x in cdf.columns]
    crashes_table = DataTable(source=csource, editable=True, width=1200, height=400, columns=ccolumns)

    charts_box = AppVBox(children=[], name='charts_box')

    counts = cdf['crashes']
    crashes_hist = charts.Histogram({'crash_counts': counts}, bins=20, height=300, title="# Crashes per Symbol")
    crashes_scatter = create_crashes_scatter()

    main_tab = VBox(children=[], name='d_box')
    dlg = Dialog(buttons=[], content=main_tab , visible=False)

    options = CheckboxGroup(
        labels=['Show peaks', 'Show Std. Dev.', 'Bolinger Bands'],
        name='new_chart_options'
    )

    select_palette = Select.create(options=brewer.keys(), name='select_palette', title="Palette")
    return {
        # security tab
        'select_sec': select_sec,
        'field_to_add': asel,
        'chart_to_add': chart_sel,
        'ms': msel,
        'dt': data_table,
        'add_button': abutton,
        'remove_button': rbutton,
        'add_chart': add_chart_button,
        'charts_box': charts_box,
        'dlg': dlg,

        # Crashes tab objs
        'crashes_hist': crashes_hist,
        'crashes_scatter': crashes_scatter,
        'crashes_table': crashes_table,
        'crash_stats': PreText(text="NO CRASHES FOR SYMBOL %s" % SYMBOL, width=300),

        #
        'chart_values': MultiSelect.create(options=df.columns, name="chart_values", title="Values"),
        'new_chart_index': Select.create(options=['---']+list(df.columns), title="Chart index", name="new_chart_index"),
        'new_chart_title': TextInput(title="Chart Title", name='new_chart_title', value=''),
        'new_chart_options': options,
        'select_palette': select_palette,

        # ANNOTATIONS
        "annotations": MultiSelect.create(options=[], name="annotations", title="Annotations"),
        "add_annotation": Button(label="add", type="success", name='add_annotation'),
        "delete_annotation": Button(label="remove", type="danger", name='delete_annotation'),
        "show_annotation": Button(label="Show", type="link", name='show_annotation'),
        'new_annotation_dlg': Dialog(buttons=[], content=main_tab , visible=False),
        'annotation_txt': TextInput(title="New Annotation", name='annotation_txt', value=''),
        'new_annotation_options': CheckboxGroup(labels=[], name='new_annotation_options'),
    }

@dashboard.layout
def dash_layout(app):
    """
    Creates the app layout
    """
    add_box = AppHBox(app=app, children=['field_to_add'])
    rem_box = AppHBox(app=app, children=['remove_button'])
    widgets = AppVBox(
        app=app,
        children=[
            'select_sec', add_box, 'add_button', 'ms', rem_box,
            'chart_to_add', 'add_chart', 'annotations', 'add_annotation',
            'delete_annotation', 'show_annotation'
        ],
        width=200
    )
    tab_stats_row =  AppHBox(app=app, children=['dt', 'dlg', 'new_annotation_dlg', 'crash_stats'])
    mainbox = AppVBox(app=app, children=[tab_stats_row, 'charts_box'], name='charts_box')
    charts_box = app.objects['charts_box']
    charts_box.app = app
    main_content = HBox(children=[widgets, mainbox])

    crashes_charts = AppHBox(app=app, children=['crashes_scatter', 'crashes_hist'])
    crashes = AppVBox(app=app, children=[crashes_charts, 'crashes_table'])

    main_tab = Panel(child=main_content, title="Symbol Anomalies")
    crashes_tab = Panel(child=crashes, title="CRASHES")

    app = Tabs(tabs=[main_tab, crashes_tab])

    return app

dashboard.route("/bokeh/dash/")

@dashboard.update([({'name' : 'add_button'}, ['clicks'])])
def dash_update_input(abutton, app):
    """
    Event handler for click on "add field" button
    """
    ms = app.objects['ms']
    dt = app.objects['dt']

    columns = [x for x in dt.columns]
    ndt = DataTable(source=source, columns=columns, editable=True, width = 500)
    new_ms = MultiSelect.create(options=[x for x in ms.options], name='ms')
    new_value = app.objects['field_to_add'].value or app.objects['field_to_add'].options[0]['value']
    rec = {'name': new_value, 'value': new_value}
    if new_value and not rec in new_ms.options:
        new_ms.options.append(rec)
        ndt.columns.append(
            TableColumn(field=new_value, title=new_value, editor=StringEditor())
        )

    return {'ms': new_ms, 'dt': ndt}

@dashboard.update([({'name': 'remove_button'}, ['clicks'])])
def dash_remove_field(rbutton, app):
    """
    Event handler for click on "remove field" button
    """
    ms = app.objects['ms']
    to_remove = ms.value
    options = [x for x in ms.options if x['value'] not in to_remove]
    new_ms = MultiSelect.create(options=options, name='ms')

    # TODO: Do we really need to recreate the entire DataTable object?
    ndt = DataTable(source=source, columns=[], editable=True, width=500)
    for new_value in options:
        ndt.columns.append(
            TableColumn(
                field=new_value['value'], title=new_value['value'],editor=StringEditor()
            )
        )

    main_content = MultiSelect.create(options=['AW', 'BS', 'C'], name='pppp')
    main_tab = AppHBox(app=app, children=[main_content], width=300)

    return {'ms': new_ms, 'dt': ndt}


@dashboard.update([({'name': 'add_chart'}, ['clicks'])])
def add_chart(abutton, app):
    """
    Event handler for click on "add chart" button
    """
    chart_type = app.objects['chart_to_add'].value or 'line'
    return factories.configs[chart_type](app, df)




@dashboard.update([({'name': 'add_annotation'}, ['clicks'])])
def add_annotation(abutton, app):
    """
    Event handler for click on "add chart" button
    """
    return actions.add_annotation(app, active_charts)


@dashboard.update([({'name': 'confirm_add_annotation'}, ['clicks'])])
def confirm_new_annotation(btn, app):
    global saved_annotations

    annotations = app.objects['annotations']
    annotation_txt = app.objects['annotation_txt'].value

    dlg = app.objects['new_annotation_dlg']
    dlg.visible = False

    new_annotations = MultiSelect.create(options=[x for x in annotations.options], name='annotations')
    rec = {'name': annotation_txt, 'value': annotation_txt}
    if annotation_txt and not rec in new_annotations.options:
        new_annotations.options.append(rec)

    saved_annotations[annotation_txt] = {
        "txt": annotation_txt,
        "charts_selection": current_selection,
    }
    #
    # for p in app.objects['charts_box'].children:
    #     import pdb; pdb.set_trace()
    #     p.text(
    #
    #         df['ind'][current_selection['1d']['indices'][0]], 0, annotation_txt,
    #         text_font_size="8pt", text_align="center", text_baseline="middle"
    #     )
    # import pdb; pdb.set_trace()
    # print "SAVED!!", saved_annotations

    return {'annotations': new_annotations}


@dashboard.update([({'name': 'show_annotation'}, ['clicks'])])
def show_annotation(btn, app):
    annotation_txt = app.objects['annotations'].value[0]
    app.select_one({'tags' : 'main_source'}).selected = saved_annotations[annotation_txt]["charts_selection"]
    # main_tab
    return {'new_annotation_dlg': Dialog(content=annotation_txt, buttons=[], visible=True)}









@dashboard.update([({'name': 'confirm_add_chart'}, ['clicks'])])
def update_select(btn, app):
    global active_charts
    chart_type = app.objects['chart_to_add'].value or 'line'

    index = app.objects["new_chart_index"].value
    values = app.objects["chart_values"].value
    title = app.objects['new_chart_title'].value
    active_options = app.objects['new_chart_options'].active
    palette = app.objects['select_palette'].value or 'Spectral'

    std_dv = 1 in active_options

    # hide dialog
    dlg = app.objects['dlg']
    dlg.visible = False

    print "IS CHART HERE?", title in active_charts
    new_chart = active_charts.get(
        title, plotting.figure(title=title, width=1000, height=300, tools=TOOLS)
    )
    print "NEW CHART!!!!", new_chart
    new_chart = factories.makers[chart_type](
        index, values, source=source, std_dv=std_dv, palette=palette, p=new_chart
    )

    active_charts[title] = new_chart

    added = False
    ccb = []
    for x in app.objects['charts_box'].children:
        if x.title != title:
            ccb.append(x)
        else:
            added = True
            ccb.append(new_chart)

    if not added:
        ccb.append(new_chart)

    charts_box = AppVBox(app=app, children=ccb, name='charts_box')

    main_tab = VBox(children=[], name='d_box')
    dlg = Dialog(content=main_tab, visible=False)

    return {'charts_box': charts_box}


@dashboard.update([({'name' : 'select_sec'}, ['value'])])
def update_select(select_sec, app):
    # TODO: Definitely needs a better design to avoid using globals...
    global source
    global csource
    global df
    global index

    ss = app.objects['select_sec'].value
    df = load_symbol(ss)

    index = df.pop('dt')

    df = df[num_columns]
    df['ind'] = list(range(len(index)))

    for name in num_columns:
        stdv = df[name].std()
        values = [stdv for x in df.index]
        df['%s_std_dv' % name] = values

    source = ColumnDataSource(df)
    source.tags = ['main_source']

    ndt = DataTable(source=source, columns=[], editable=True, width=500)
    charts_box = AppVBox(app=app, children=[], name='charts_box')

    templ = """FOUND %s CRASHES FOR SYMBOL %s"""
    crashes_info = check_for_crash(ss)

    crashes_source = ColumnDataSource(crashes_info)
    ccolumns = [TableColumn(field=x, title=x, editor=NumberEditor()) for x in crashes_info.columns]
    txt = PreText(text=templ % (len(crashes_info), ss), width=500, height=100)
    crashes_dt = DataTable(source=crashes_source, columns=ccolumns, editable=True, width=500)

    crashes_box = AppVBox(app=app, children=[txt, crashes_dt], name='crash_stats')

    new_ms = MultiSelect.create(options=[], name='ms')
    return {
        'charts_box': charts_box,
        'dt': ndt,
        'crash_stats': crashes_box,
        'ms': new_ms,
    }

def check_for_crash(sec):
    fullsec = '%s,(non_opt)' % sec
    ncdf = cdf[cdf.sec == fullsec]
    return ncdf



@dashboard.update([({'tags' : 'main_source'}, ['selected'])])
def stock2_update_selection(sel, app):
    global current_selection

    current_selection = app.select_one({'tags' : 'main_source'}).selected

#########################
#
# Experimental! Code below is not intended to be functional
#
#########################


class Ext(object):
    def __init__(self):
        xyvalues = OrderedDict(
            python=[2, 3, 7, 5, 26, 221, 44, 233, 254, 265, 266, 267, 120, 111],
            pypy=[12, 33, 47, 15, 126, 121, 144, 233, 254, 225, 226, 267, 110, 130],
            jython=[22, 43, 10, 25, 26, 101, 114, 203, 194, 215, 201, 227, 139, 160],
        )
        self.plot = Area(
            xyvalues, title="Area Chart",
            xlabel='time', ylabel='memory',
            stacked=True, legend="top_left"
        )
        self.create_layout()

    def create_layout(self):
        self.plot_selector = Select.create(
            title="PlotType",
            name="plot_type",
            value='area',
            options=['area', "line", "scatter", "bar"],
        )

        self.btn_confirm = Button(label='add plot')
        self.layout = vplot(hplot(self.plot_selector, self.btn_confirm), self.plot)


@bokeh_app.route("/bokeh/crossfilter/")
@object_page("crossfilter")
def make_crossfilter():
    autompg['cyl'] = autompg['cyl'].astype(str)
    autompg['origin'] = autompg['origin'].astype(str)

    # area  = Ext()
    app = CrossFilter.create(df=autompg)#, exts={"TRY": area})#, sources={'AutoMPG': autompg, 'Flowers': df_fl})
    return app

