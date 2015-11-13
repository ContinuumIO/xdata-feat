from bokeh import plotting
from six import string_types

from bokeh.models.widgets import VBox, HBox, Paragraph, Button, TableColumn, DataTable, DateEditor, DateFormatter, IntEditor,\
    Select, DataTable, TableColumn, StringFormatter, NumberFormatter, StringEditor, IntEditor, NumberEditor, \
    SelectEditor, MultiSelect, Panel, Tabs

from bokeh.models.widgets import (HBox, VBox, VBoxForm, PreText, Dialog, TextInput, AutocompleteInput,
                                  Select, AppHBox, AppVBox, AppVBoxForm, CheckboxGroup)
from bokeh.palettes import brewer

def add_annotation(app, plots):
    options = CheckboxGroup(
        labels=['save selection'],
        name='new_annotation_options'
    )

    annotation = TextInput(
        title="Text", name='annotation_txt', value=""
    )

    main_tab = AppVBox(app=app, children=[options, annotation])
    confirm_chart_button = Button(label="Confirm", type="success", name='confirm_add_annotation')

    return {
        'new_annotation_dlg': Dialog(buttons=[confirm_chart_button], content=main_tab, visible=True),
        'annotation_txt': annotation,
        'new_annotation_options': options
    }