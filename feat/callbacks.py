symbol_filter = """
    msg = {
        activity: 'select',
        action: 'click',
        elementType: 'dropdownlist',
        elementId: 'symbol_filter',
        elementGroup: 'input_group',
        source: 'user',
        tags: ['query']
    };
    console.log(msg);
    ale.log(msg);

    window.prev_loaded_flag = 'changed'; //$('select[name=symbol_filter]')[0].id

    $("body").addClass("loading");
    check_loaded();
"""
source_stocks_rank = """
    $('#stocks_list_dialog').removeClass('modalTarget');

    $("body").addClass("loading");

    msg = {
        activity: 'select',
        action: 'click',
        elementType: 'datagrid',
        elementId: 'symbols_table',
        elementGroup: 'table_group',
        source: 'user',
        tags: ['query']
    };
    console.log(msg);
    ale.log(msg);

    ind = sr.get('selected')['1d']['indices'][0];
    data = sr.get('data');

    window.location.href = "/?symbol=" + data['symbol'][ind];

    $("body").addClass("loading");
    var loadingDiv = document.getElementById('loadingDiv');
    if (!!loadingDiv) {
        loadingDiv.style.display = 'block';
        var loadingTextDiv = loadingDiv.firstElementChild;
        var count = 0;
        var animateLoading = function() {
            setInterval(function(){
                    if (count > 2) {
                        loadingTextDiv.innerHTML = "Loading";
                        count = 0;
                    }
                    else {
                        loadingTextDiv.innerHTML += ".";
                        count++;
                    }
                 }, 450);

        }
        animateLoading();
    }
"""

btn_detect_pumps = """

    PEAKS.set('visible', true);
    msg = {
        activity: 'select',
        action: 'click',
        elementType: 'button',
        elementId: 'btn_detect_pumps',
        elementGroup: 'query_group',
        source: 'user',
        tags: ['query']
    };
    ale.log(msg);
"""

window_selector = """
    plugins = %(js_list_of_sources)s;
    if (plugins[interval_selector.get('value')]!=undefined){
        plugin = plugins[interval_selector.get('value')];
        plugin.set('visible', true)
    }
"""


small_selection_plot = """
    window.ss = spark_source; //mr._set_start(10)

    data = spark_source.get('data')
    sel = spark_source.get('selected')['1d']['indices']
    var mi = 1000000000;
    var ma = -100000;
    var values = [];
    var values_vol_var = [];
    var values_price_var = [];

    // Get main plot ranges
    if (Bokeh.Collections('Plot').models[0].get("plot_height") == 350){
        var main_plot = Bokeh.Collections('Plot').models[0];
    }else{
        var main_plot = Bokeh.Collections('Plot').models[1];
    }
    main_range = main_plot.get('x_range');
    main_y_range = main_plot.get('y_range');

    for (i=0; i<sel.length; i++){
        if (mi>sel[i]){
            mi = sel[i];
        }
        if (ma<sel[i]){
            ma = sel[i];
        }
        values.push(data.price[sel[i]]);
        values_vol_var.push(data.vol_delta[sel[i]]);
        values_price_var.push(data.price_delta[sel[i]]);
    }

    if (window.xrange_base_start == undefined){
        window.xrange_base_start = main_range.get('start');
    }
    if (window.xrange_base_end == undefined){
        window.xrange_base_end = main_range.get('end');
    }
    if (window.yrange_base_start == undefined){
        window.yrange_base_start = main_y_range.get('start');
    }
    if (window.yrange_base_end == undefined){
        window.yrange_base_end = main_y_range.get('end');
    }


    var range_start = Math.min.apply(null, values);
    var range_end = Math.max.apply(null, values);

    if (sel.length==0){
        main_range.set('start', window.xrange_base_start);
        main_range.set('end', window.xrange_base_end);
        main_y_range.set('start', window.yrange_base_start);
        main_y_range.set('end', window.yrange_base_end);
    }else{
        main_y_range.set('start', range_start - range_start * 0.1);
        main_y_range.set('end', range_end + range_end * 0.1);
        main_range.set('start', data.dt[mi]);
        main_range.set('end', data.dt[ma]);
    }

    var spams_found = [];
    var des = evts_source.get('data');

    if (des.sdt != undefined){
        for (i=0; i<des.sdt.length; i++){
            if (des.sdt[i] >= data.dt[mi] && des.sdt[i] <= data.dt[ma]){
                spams_found.push({'date': des.sdt[i]});
            }
        }
    }

    if (sel.length==0){
        $("#plugins_wrapper").addClass("hidden");
        $("#details_panel").html("");
    }else{
        $("#plugins_wrapper").removeClass("hidden");
        $("#details_panel").html("<h3>Selected Region Report</h3>");
        $("#details_panel").append("<div>From " + data.exch_ts[mi] + " to " + data.exch_ts[ma] + "</div>");
        $("#details_panel").append("<div>" + spams_found.length + " spams (from a total of " + des.sdt.length + ") have been found in the selected period</div>");
    }
    // fill the rect glyph to show the current selection
    source_data = selection_source.get('data');
    source_data.bottom = [0]
    source_data.values = [%s];
    source_data.start = [data.dt[mi]];
    source_data.end = [data.dt[ma]];
    selection_source.trigger('change');

    msg = {
        activity: 'select',
        action: 'zoom',
        elementType: 'canvas',
        elementId: 'small_plot',
        elementGroup: 'chart_group',
        source: 'user',
        tags: ['query']
    };
    ale.log(msg);
"""

line_hover = """
    msg = {
        activity: 'inspect',
        action: 'mouseover',
        elementType: 'canvas',
        elementId: 'price_line',
        elementGroup: 'chart_group',
        source: 'user',
        tags: ['query']
    };
    ale.log(msg);
"""