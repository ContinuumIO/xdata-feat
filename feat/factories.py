from bokeh import plotting
from six import string_types

from bokeh.models.widgets import VBox, HBox, Paragraph, Button, TableColumn, DataTable, DateEditor, DateFormatter, IntEditor,\
    Select, DataTable, TableColumn, StringFormatter, NumberFormatter, StringEditor, IntEditor, NumberEditor, \
    SelectEditor, MultiSelect, Panel, Tabs

from bokeh.models.widgets import (HBox, VBox, VBoxForm, PreText, Dialog, TextInput, AutocompleteInput,
                                  Select, AppHBox, AppVBox, AppVBoxForm, CheckboxGroup)
from bokeh.palettes import brewer

def line_config(app, df):
    options = CheckboxGroup(
        labels=['Show peaks', 'Show Std. Dev.', 'Bolinger Bands'],
        name='new_chart_options'
    )

    title = TextInput(title="Chart Title", name='new_chart_title', value="Line")
    new_chart_index = Select.create(options=['---']+list(df.columns), name='"new_chart_index"', title="Chart index")
    chart_values_select = MultiSelect.create(options=df.columns, name="chart_values", title="Values")
    chart_data = AppHBox(app=app, children=[new_chart_index, chart_values_select, options])
    main_tab = AppVBox(app=app, children=[title, chart_data, 'select_palette'])
    confirm_chart_button = Button(label="Confirm", type="success", name='confirm_add_chart')

    return {
        'dlg': Dialog(buttons=[confirm_chart_button], content=main_tab, visible=True),
        "new_chart_index": new_chart_index,
        'new_chart_title': title,
        'chart_values': chart_values_select,
        'new_chart_options': options
    }

def line_config(app, df):
    options = CheckboxGroup(
        labels=['Show peaks', 'Show Std. Dev.', 'Bolinger Bands'],
        name='new_chart_options'
    )

    title = TextInput(
        title="Chart Title", name='new_chart_title', value="Line"
    )

    new_chart_index = Select.create(options=['---']+list(df.columns), name='"new_chart_index"', title="Chart index")
    chart_values_select = MultiSelect.create(options=df.columns, name="chart_values", title="Values")

    chart_data = AppHBox(app=app, children=[new_chart_index, chart_values_select, options])
    main_tab = AppVBox(app=app, children=[title, chart_data, 'select_palette'])
    confirm_chart_button = Button(label="Confirm", type="success", name='confirm_add_chart')

    return {
        'dlg': Dialog(buttons=[confirm_chart_button], content=main_tab, visible=True),
        "new_chart_index": new_chart_index,
        'new_chart_title': title,
        'chart_values': chart_values_select,
        'new_chart_options': options
    }


def create_line(index, values, source=None,
                palette="Spectral", std_dv=False, p=None, colors=None):
    if not colors:
        colors = brewer[palette][max(len(values), 3)]

    if index in ['---', None]:
        index = 'ind'

    for i, name in enumerate(values):
        p.line(index, name, color=colors[i], line_width=1, source=source)

        if std_dv:
            p.line(
                index, '%s_std_dv' % name, color=colors[i], line_width=2,
                source=source, line_dash="dashed", line_alpha=0.8,
            )

    return p


def scatter(index, values, source=None, palette="Spectral", std_dv=False, p=None, **kws):
    if p is None:
        p = plotting.figure(title=title)

    colors = kws.pop('colors', brewer[palette][max(len(values), 3)])

    if index in ['---', None]:
        index = ['ind'] * len(values)
    elif isinstance(index, string_types):
        index = [index] * len(values)

    for i, (ind, name) in enumerate(zip(index, values)):
        p.circle(ind, name, fill_color=colors[i], fill_alpha=0.6, line_color=None, source=source)

    return p


def band(index, values, source=None, palette="Spectral", p=None, **kws):
    import numpy as np
    if p is None:
        p = plotting.figure(title=title)

    colors = kws.pop('colors', brewer[palette][max(len(values), 3)])

    if index in ['---', None]:
        index = 'ind'

    band_x = np.append(source.data[index], source.data[index][::-1])
    band_y = np.append(source.data[values[0]], source.data[values[1]][::-1])

    p.patch(band_x, band_y, color=colors[0], fill_alpha=0.2)
    return p


configs = {
    'line': line_config,
    'scatter': line_config,
    'band': line_config,
}

makers = {
    'line': create_line,
    'scatter': scatter,
    'band': band,
}