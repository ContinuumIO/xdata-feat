import pandas as pd

def compute_quotient_metrics(filename,
                             index_col=0,
                             resample_period='1M',
                             shift=0,
                             quotient_metrics=[('Volume', 'max', 'median'),
                                               ('Close', 'max', 'min')]):

    """Compute quotient metrics from CSV data.
    
    Quotient metrices are given in the form: (Name, Num, Den), where Name is
    the  corresponding column from the CSV file to be measured, Num is the
    metric to be  used as the numerator, and Den is the metric to be used as
    the denominator.
    
    The column specified by index_col is assumed to contain the dates, which
    are  then binned each metric over the resample period.  By default, the
    metrics are  computed for the same time period, but this can be changed by
    setting the shift  value.  For example, setting shift=1 will cause the
    metric computed for February  to be divided by the metric computed in
    January.

    For example:

    compute_quotient_metrics(filename, index_col=0, resample_period='1M',
                             shift=0, quotient_metrics = [('Volume', 'max',
                             'median'), ('Close', 'max', 'min')]):

    computes for each month in the data, the maximum volume divided by the
    median volume, and the maximum close price over the minimum close price.

    The output metrics can be further reduced by computing the maximum monthly
    metric.
    
    See pandas.series.resample for examples of valid resample periods and
    metrics.
    """
    
    data = pd.read_csv(filename, index_col=index_col, parse_dates=True)
    
    def compute_quotient_metric(name, num_metric, den_metric):
        series = pd.TimeSeries(data[name])
        num_period = series.resample(resample_period, how=num_metric)
        den_period = series.resample(resample_period, how=den_metric)
        return num_period[shift:]/den_period[:len(num_period)-shift].values

    return [compute_quotient_metric(*qm) for qm in quotient_metrics]



if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
       for file in sys.argv[1:]:
          v, p = compute_quotient_metrics(file, shift=1)
          print "Maximum Monthly Volume Max/Median for %s : %6.6g" % (file, v.max())
          print "Maximum Monthly Close Price Max/Min for %s: %6.6g" % (file, p.max())
