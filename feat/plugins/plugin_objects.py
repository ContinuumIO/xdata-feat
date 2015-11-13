import bokeh.models as __mo

spam = __mo.Instance(__mo.Slider)
spam_source = __mo.Instance(__mo.ColumnDataSource)
hspam_source = __mo.Instance(__mo.ColumnDataSource)
hspam_sources = __mo.List(__mo.Instance(__mo.ColumnDataSource))
spam_tab = __mo.Instance(__mo.Panel)
spam_table = __mo.Instance(__mo.DataTable)

news = __mo.Instance(__mo.Slider)
news_source = __mo.Instance(__mo.ColumnDataSource)
hnews_source = __mo.Instance(__mo.ColumnDataSource)
hnews_sources = __mo.List(__mo.Instance(__mo.ColumnDataSource))
news_tab = __mo.Instance(__mo.Panel)
news_table = __mo.Instance(__mo.DataTable)

PEAKS =  __mo.Instance(__mo.Dialog)
PEAKS_source = __mo.Instance(__mo.ColumnDataSource)
PEAKS_content = __mo.Instance(__mo.VBox)
# peaks_min_duration = __mo.Instance(__mo.TextInput)
PEAKS_min_quiet_days = __mo.Instance(__mo.TextInput)
PEAKS_quiet_tol = __mo.Instance(__mo.TextInput)
PEAKS_min_growth_days = __mo.Instance(__mo.TextInput)
PEAKS_max_growth_days = __mo.Instance(__mo.TextInput)
PEAKS_growth_tols = __mo.Instance(__mo.TextInput)

PEAKS_confirm_button = __mo.Instance(__mo.Button)

# TICKS_IN_ROW = __mo.Instance(__mo.Dialog)
# TICKS_IN_ROW_source = __mo.Instance(__mo.ColumnDataSource)
# TICKS_IN_ROW_content = __mo.Instance(__mo.VBox)
# TICKS_IN_ROW_limit = __mo.Instance(__mo.TextInput)
# TICKS_IN_ROW_confirm_button = __mo.Instance(__mo.Button)