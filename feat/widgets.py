from __future__ import print_function

from bokeh.models.actions import Callback
from bokeh.models.widgets import Slider

def create_evts_widget(objs, evts_source, hevts_source, **kws):
    javascript_list_of_sources = str(list(objs.keys())).replace("'", "")
    slen = len(objs)

    code = """
        var new_selection = [];
        for (var i = 0; i < spam_slider.get('value'); i++) {
            new_selection.push(i);
        }
        var new_selection_object = {
            '0d': {'flag': false, 'indices': []},
            '1d': {'indices': new_selection},
            '2d': {'indices': []}
        };

        evts_source.attributes.selected = new_selection_object;
        evts_source.trigger('change');

        if (spam_slider.get('value') == 0) {
            hevts_source.get('data').top = hevts_source.get('data').bottom;
        } else {
            var sources = %s;

            ss = sources[spam_slider.get('value')];
            hevts_source.get('data').top = ss.get('data').real_top;

        }
        hevts_source.trigger('change');

    """ % javascript_list_of_sources

    objs['evts_source'] = evts_source
    objs['hevts_source'] = hevts_source

    callback = Callback(args=objs, code=code)

    slider = Slider(
        value=0, start=0, end=slen, step=1, callback=callback,
        **kws
    )
    callback.args["spam_slider"] = slider
    return slider